import os
import logging
import base64
import requests as http
from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import db, User, VM, Configuration, OSImage

app = Flask(__name__)
app.config.from_object(Config)
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))



OPENSTACK_API = "https://cp.gpucloud.ru/api/openstack/moscowone/nova/v2.1"


_USER_DATA_TEMPLATE = (
    'Content-Type: multipart/mixed; boundary="===============2309984059743762475==" \n'
    'MIME-Version: 1.0\n'
    '\n'
    '--===============2309984059743762475==\n'
    'Content-Type: text/cloud-config; charset="us-ascii" \n'
    'MIME-Version: 1.0\n'
    'Content-Transfer-Encoding: 7bit\n'
    'Content-Disposition: attachment; filename="ssh-pwauth-script.txt" \n'
    '\n'
    '#cloud-config\n'
    'disable_root: false\n'
    'ssh_pwauth: true\n'
    'password: {password}\n'
    '\n'
    '--===============2309984059743762475==\n'
    'Content-Type: text/x-shellscript; charset="us-ascii" \n'
    'MIME-Version: 1.0\n'
    'Content-Transfer-Encoding: 7bit\n'
    'Content-Disposition: attachment; filename="passwd-script.txt" \n'
    '\n'
    '#!/bin/sh\n'
    "echo 'root:{password}' | chpasswd\n"
    '\n'
    '--===============2309984059743762475==--\n'
)


def build_user_data(password: str) -> str:
    text = _USER_DATA_TEMPLATE.format(password=password)
    return base64.b64encode(text.encode('utf-8')).decode('utf-8')


def openstack_headers() -> dict:
    return {
        'X-Auth-Token': os.getenv('OPENSTACK_TOKEN'),
        'Content-Type': 'application/json',
        'Openstack-Api-Version': 'compute 2.79',
    }


def get_flavor_id(vcpu: int, ram_gb: int) -> str | None:
    """Найти flavorRef по vCPU и RAM из таблицы configurations."""
    name = f"amd-{vcpu}-{ram_gb}"
    config = db.session.get(Configuration, name)
    return config.id if config else None

def get_vm_state(openstack_id: str) -> dict:
    """Запросить состояние ВМ из OpenStack. Возвращает {'status': str, 'ip': str|None}."""
    try:
        resp = http.get(f"{OPENSTACK_API}/servers/{openstack_id}",
                        headers=openstack_headers(), timeout=10)
        if resp.status_code != 200:
            return {'status': 'unknown', 'ip': None}
        data = resp.json()['server']
        os_status = data.get('status', 'UNKNOWN')
        if os_status == 'ACTIVE':
            status = 'running'
        elif os_status in ('SHUTOFF', 'STOPPED'):
            status = 'stopped'
        elif os_status in ('BUILD', 'REBUILD', 'REBOOT', 'HARD_REBOOT'):
            status = 'building'
        elif os_status == 'ERROR':
            status = 'error'
        else:
            status = 'unknown'
        ip = None
        for addrs in data.get('addresses', {}).values():
            for a in addrs:
                if a.get('version') == 4:
                    ip = a.get('addr')
                    break
            if ip:
                break
        return {'status': status, 'ip': ip}
    except http.exceptions.RequestException:
        return {'status': 'unknown', 'ip': None}



@app.route('/')
def index():
    return render_template('main_page/index.html')



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if not all([username, email, password, confirm]):
            flash('Заполните все поля', 'error')
            return redirect(url_for('register'))

        if password != confirm:
            flash('Пароли не совпадают', 'error')
            return redirect(url_for('register'))

        if len(password) < 8:
            flash('Пароль должен быть не менее 8 символов', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Имя пользователя уже занято', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email уже используется', 'error')
            return redirect(url_for('register'))

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Аккаунт создан — войдите в систему', 'success')
        return redirect(url_for('login'))

    return render_template('reg_auth_page/index.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin') if current_user.is_admin else url_for('account'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()

        if user is None or not user.check_password(password):
            flash('Неверный email или пароль', 'error')
            return redirect(url_for('login'))

        if not user.is_active:
            flash('Аккаунт заблокирован', 'error')
            return redirect(url_for('login'))

        login_user(user)
        return redirect(url_for('admin') if user.is_admin else url_for('account'))

    return render_template('auth_page/login.html')


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/account')
@login_required
def account():
    vms = VM.query.filter_by(user_id=current_user.id).order_by(VM.created_at.desc()).all()
    quotas = {
        'vms_used':  len(vms),
        'vms_max':   5,
        'vcpu_used': sum(v.vcpu for v in vms),
        'vcpu_max':  20,
        'ram_used':  sum(v.ram for v in vms),
        'ram_max':   40,
        'ssd_used':  sum(v.ssd for v in vms),
        'ssd_max':   500,
    }
    return render_template('account_page/index.html', vms=vms, quotas=quotas)


@app.route('/account/import', methods=['POST'])
@login_required
def import_vms():
    import json as json_lib
    file = request.files.get('file')
    if not file or not file.filename.endswith('.json'):
        flash('Загрузите файл в формате .json', 'error')
        return redirect(url_for('account'))

    try:
        configs = json_lib.loads(file.read().decode('utf-8'))
        if not isinstance(configs, list):
            raise ValueError
    except Exception:
        flash('Неверный формат файла', 'error')
        return redirect(url_for('account'))

    existing_vms = VM.query.filter_by(user_id=current_user.id).all()
    used = {
        'vms':  len(existing_vms),
        'vcpu': sum(v.vcpu for v in existing_vms),
        'ram':  sum(v.ram  for v in existing_vms),
        'ssd':  sum(v.ssd  for v in existing_vms),
    }
    limits = {'vms': 5, 'vcpu': 20, 'ram': 40, 'ssd': 500}

    created, skipped = 0, []

    for cfg in configs:
        name    = str(cfg.get('name', '')).strip()
        os_name = str(cfg.get('os', 'Ubuntu'))
        vcpu    = int(cfg.get('vcpu', 1))
        ram     = int(cfg.get('ram_gb', 1))
        ssd     = int(cfg.get('ssd_gb', 10))

        if not name:
            skipped.append('(без имени) — нет имени')
            continue

        if used['vms']  + 1    > limits['vms']:
            skipped.append(f'{name} — превышен лимит ВМ')
            continue
        if used['vcpu'] + vcpu  > limits['vcpu']:
            skipped.append(f'{name} — превышен лимит vCPU')
            continue
        if used['ram']  + ram   > limits['ram']:
            skipped.append(f'{name} — превышен лимит RAM')
            continue
        if used['ssd']  + ssd   > limits['ssd']:
            skipped.append(f'{name} — превышен лимит SSD')
            continue

        flavor_id = get_flavor_id(vcpu, ram)
        if not flavor_id:
            skipped.append(f'{name} — нет flavor для {vcpu} vCPU / {ram} GB RAM')
            continue

        image = db.session.get(OSImage, os_name)
        if not image:
            skipped.append(f'{name} — образ {os_name} не найден')
            continue

        payload = {"server": {
            "security_groups": [{"name": os.getenv('OPENSTACK_SECURITY_GROUP')}],
            "name": name, "flavorRef": flavor_id, "availability_zone": "nova",
            "networks": [{"uuid": os.getenv('OPENSTACK_NETWORK_UUID')}],
            "block_device_mapping_v2": [{"boot_index": 0, "uuid": image.uuid,
                "source_type": "image", "volume_size": ssd,
                "destination_type": "volume", "delete_on_termination": True,
                "volume_type": os.getenv('OPENSTACK_VOLUME_TYPE')}],
        }}

        try:
            resp = http.post(f"{OPENSTACK_API}/servers", json=payload,
                             headers=openstack_headers(), timeout=30)
        except http.exceptions.RequestException:
            skipped.append(f'{name} — нет связи с OpenStack')
            continue

        if resp.status_code not in (200, 202):
            skipped.append(f'{name} — ошибка OpenStack: {resp.status_code}')
            continue

        openstack_id = resp.json()['server']['id']
        vm = VM(user_id=current_user.id, openstack_id=openstack_id,
                name=name, os=os_name, vcpu=vcpu, ram=ram, ssd=ssd, status='building')
        db.session.add(vm)
        db.session.commit()

        used['vms']  += 1
        used['vcpu'] += vcpu
        used['ram']  += ram
        used['ssd']  += ssd
        created += 1

    if created:
        flash(f'Создано виртуальных машин: {created}', 'success')
    for msg in skipped:
        flash(f'Пропущено: {msg}', 'error')

    return redirect(url_for('account'))


@app.route('/account/export')
@login_required
def export_vms():
    from flask import jsonify
    vms = VM.query.filter_by(user_id=current_user.id).order_by(VM.created_at.desc()).all()
    data = [{
        'name':         vm.name,
        'os':           vm.os,
        'vcpu':         vm.vcpu,
        'ram_gb':       vm.ram,
        'ssd_gb':       vm.ssd,
        'status':       vm.status,
        'openstack_id': vm.openstack_id,
        'created_at':   vm.created_at.isoformat() if vm.created_at else None,
    } for vm in vms]
    response = jsonify(data)
    response.headers['Content-Disposition'] = 'attachment; filename="vms.json"'
    return response


@app.route('/create-vm', methods=['GET', 'POST'])
@login_required
def create_vm():
    if request.method == 'POST':
        vm_name    = request.form.get('vm_name', '').strip()
        os_name    = request.form.get('os', 'Ubuntu')
        vcpu       = int(request.form.get('vcpu', 1))
        ram        = int(request.form.get('ram', 1))
        ssd        = int(request.form.get('ssd', 10))
        vm_password = request.form.get('vm_password', '')

        app.logger.info(f"[create_vm] name={vm_name} os={os_name} vcpu={vcpu} ram={ram} ssd={ssd}")

        existing = VM.query.filter_by(user_id=current_user.id).all()
        if len(existing) >= 5:
            flash('Превышена квота: максимум 5 виртуальных машин', 'error')
            return redirect(url_for('create_vm'))
        if sum(v.vcpu for v in existing) + vcpu > 20:
            flash(f'Превышена квота: максимум 20 vCPU (используется {sum(v.vcpu for v in existing)})', 'error')
            return redirect(url_for('create_vm'))
        if sum(v.ram for v in existing) + ram > 40:
            flash(f'Превышена квота: максимум 40 GB RAM (используется {sum(v.ram for v in existing)} GB)', 'error')
            return redirect(url_for('create_vm'))
        if sum(v.ssd for v in existing) + ssd > 500:
            flash(f'Превышена квота: максимум 500 GB SSD (используется {sum(v.ssd for v in existing)} GB)', 'error')
            return redirect(url_for('create_vm'))

        flavor_id = get_flavor_id(vcpu, ram)
        app.logger.info(f"[create_vm] flavor_id={flavor_id}")
        if not flavor_id:
            flash(f'Нет доступного flavor для {vcpu} vCPU и {ram} GB RAM', 'error')
            return redirect(url_for('create_vm'))

        image = db.session.get(OSImage, os_name)
        app.logger.info(f"[create_vm] image={image}")
        if not image:
            flash(f'Образ {os_name} не найден в базе данных', 'error')
            return redirect(url_for('create_vm'))
        image_uuid = image.uuid

        payload = {
            "server": {
                "security_groups": [{"name": os.getenv('OPENSTACK_SECURITY_GROUP')}],
                "name": vm_name,
                "flavorRef": flavor_id,
                "availability_zone": "nova",
                "networks": [{"uuid": os.getenv('OPENSTACK_NETWORK_UUID')}],
                "block_device_mapping_v2": [{
                    "boot_index": 0,
                    "uuid": image_uuid,
                    "source_type": "image",
                    "volume_size": ssd,
                    "destination_type": "volume",
                    "delete_on_termination": True,
                    "volume_type": os.getenv('OPENSTACK_VOLUME_TYPE')
                }],
                "adminPass": vm_password,
                "user_data": build_user_data(vm_password),
            }
        }

        try:
            resp = http.post(
                f"{OPENSTACK_API}/servers",
                json=payload,
                headers=openstack_headers(),
                timeout=30,
            )
        except http.exceptions.RequestException as e:
            app.logger.error(f"[create_vm] RequestException: {e}")
            flash('Нет связи с OpenStack API', 'error')
            return redirect(url_for('create_vm'))

        app.logger.info(f"[create_vm] OpenStack status={resp.status_code} body={resp.text[:300]}")

        if resp.status_code not in (200, 202):
            error_msg = resp.json().get('badRequest', {}).get('message') or resp.text
            flash(f'Ошибка OpenStack: {error_msg}', 'error')
            return redirect(url_for('create_vm'))

        openstack_id = resp.json()['server']['id']

        vm = VM(
            user_id=current_user.id,
            openstack_id=openstack_id,
            name=vm_name,
            os=os_name,
            vcpu=vcpu,
            ram=ram,
            ssd=ssd,
            status='building',
        )
        db.session.add(vm)
        db.session.commit()

        flash(f'Виртуальная машина «{vm_name}» создаётся', 'success')
        return redirect(url_for('account'))

    return render_template('create_vm_page/index.html')


@app.route('/vm/<int:vm_id>')
@login_required
def vm_settings(vm_id):
    vm = db.session.get(VM, vm_id)
    if vm is None:
        abort(404)
    if vm.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    return render_template('vm_page/index.html', vm=vm)


@app.route('/api/vm/<int:vm_id>/status')
@login_required
def vm_status_api(vm_id):
    from flask import jsonify
    vm = db.session.get(VM, vm_id)
    if vm is None or (vm.user_id != current_user.id and not current_user.is_admin):
        return jsonify({'error': 'not found'}), 404
    state = get_vm_state(vm.openstack_id)
    if state['status'] != 'unknown':
        vm.status = state['status']
        db.session.commit()
    return jsonify(state)


@app.route('/vm/<int:vm_id>/start', methods=['POST'])
@login_required
def vm_start(vm_id):
    from flask import jsonify
    vm = db.session.get(VM, vm_id)
    if vm is None or (vm.user_id != current_user.id and not current_user.is_admin):
        return jsonify({'error': 'forbidden'}), 403
    resp = http.post(f"{OPENSTACK_API}/servers/{vm.openstack_id}/action",
                     json={"os-start": None},
                     headers=openstack_headers(), timeout=10)
    if resp.status_code in (200, 202):
        return jsonify({'ok': True})
    return jsonify({'error': resp.text}), 502


@app.route('/vm/<int:vm_id>/stop', methods=['POST'])
@login_required
def vm_stop(vm_id):
    from flask import jsonify
    vm = db.session.get(VM, vm_id)
    if vm is None or (vm.user_id != current_user.id and not current_user.is_admin):
        return jsonify({'error': 'forbidden'}), 403
    resp = http.post(f"{OPENSTACK_API}/servers/{vm.openstack_id}/action",
                     json={"os-stop": None},
                     headers=openstack_headers(), timeout=10)
    if resp.status_code in (200, 202):
        return jsonify({'ok': True})
    return jsonify({'error': resp.text}), 502


@app.route('/vm/<int:vm_id>/console', methods=['POST'])
@login_required
def vm_console(vm_id):
    from flask import jsonify
    vm = db.session.get(VM, vm_id)
    if vm is None or (vm.user_id != current_user.id and not current_user.is_admin):
        return jsonify({'error': 'forbidden'}), 403
    headers = {
        'X-Auth-Token': os.getenv('OPENSTACK_TOKEN'),
        'Content-Type': 'application/json',
        'Openstack-Api-Version': 'compute 2.79',
    }
    resp = http.post(
        f"{OPENSTACK_API}/servers/{vm.openstack_id}/remote-consoles",
        data="""{"remote_console": {"protocol": "vnc", "type": "novnc"}}""",
        headers=headers, timeout=10,
    )

    app.logger.info(f"[console] status={resp.status_code} instance={vm.openstack_id} body={resp.text[:500]}")
    if resp.status_code in (200, 202):
        url = resp.json().get('remote_console', {}).get('url')
        return jsonify({'url': url})
    return jsonify({'error': resp.text}), 502


@app.route('/vm/<int:vm_id>/delete', methods=['POST'])
@login_required
def vm_delete(vm_id):
    vm = db.session.get(VM, vm_id)
    if vm is None or (vm.user_id != current_user.id and not current_user.is_admin):
        abort(403)
    http.post(
        f"{OPENSTACK_API}/servers/{vm.openstack_id}/action",
        json={"forceDelete": None},
        headers=openstack_headers(), timeout=10,
    )
    db.session.delete(vm)
    db.session.commit()
    return redirect(url_for('account'))


@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        abort(403)

    users = User.query.order_by(User.created_at.desc()).all()
    for u in users:
        u.vm_count = len(u.vms)
        u.vcpu_used = sum(v.vcpu for v in u.vms)
        u.ram_used = sum(v.ram for v in u.vms)
        u.ssd_used = sum(v.ssd for v in u.vms)

    stats = {
        'total_users': len(users),
        'total_vms': sum(u.vm_count for u in users),
        'total_vcpu': sum(u.vcpu_used for u in users),
        'total_ram': sum(u.ram_used for u in users),
        'total_ssd': sum(u.ssd_used for u in users),
    }

    return render_template('admin_page/index.html', users=users, stats=stats)


@app.route('/admin/user/<int:user_id>')
@login_required
def admin_user(user_id):
    if not current_user.is_admin:
        abort(403)

    user = db.session.get(User, user_id)
    if user is None:
        abort(404)

    vms = VM.query.filter_by(user_id=user.id).order_by(VM.created_at.desc()).all()
    quotas = {
        'vms_used': len(vms), 'vms_max': 5,
        'vcpu_used': sum(v.vcpu for v in vms), 'vcpu_max': 20,
        'ram_used': sum(v.ram for v in vms), 'ram_max': 40,
        'ssd_used': sum(v.ssd for v in vms), 'ssd_max': 500,
    }

    return render_template('admin_page/user_detail.html', user=user, vms=vms, quotas=quotas)


if __name__ == '__main__':
    app.run(host='localhost', debug=False)
