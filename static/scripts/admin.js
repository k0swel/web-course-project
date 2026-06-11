const searchInput = document.getElementById('search');
const userList = document.getElementById('user-list');
const usersCount = document.getElementById('users-count');
const rows = Array.from(userList.querySelectorAll('.user-row'));

searchInput.addEventListener('input', function () {
    const query = this.value.toLowerCase().trim();
    let visible = 0;

    rows.forEach(row => {
        const match = row.dataset.search.includes(query);
        row.style.display = match ? '' : 'none';
        if (match) visible++;
    });

    usersCount.textContent = `${visible} пользователей`;
});
