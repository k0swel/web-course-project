function update_price() {
    const SSD_UNIT_PRICE=10;
    const VCPUS_UNIT_PRICE=1000;
    const RAM_UNIT_PRICE=500;

    const vcpus_count = document.getElementById('vcpus_range').value;
    const ram_count = document.getElementById('ram_range').value;
    const ssd_count = document.getElementById('ssd_range').value;


    const price_tag = document.getElementById('price');
    price_tag.textContent = calculate_price(vcpus_count, ram_count, ssd_count, VCPUS_UNIT_PRICE, RAM_UNIT_PRICE, SSD_UNIT_PRICE);
}

document.addEventListener('DOMContentLoaded', () => {
    update_price();;
})

document.querySelectorAll('.specs').forEach((element) => element.addEventListener('input', () => {update_price();}));

function calculate_price(vcpus, ram, ssd, vcpus_price, ram_price, ssd_price) {
    return vcpus * vcpus_price + ram * ram_price + ssd * ssd_price;
} 