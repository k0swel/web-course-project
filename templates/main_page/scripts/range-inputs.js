document.querySelectorAll('input[type="range"]').forEach(input => {
    const output = document.getElementById(input.id.replace('_range', '_value'));
    input.addEventListener('input', () => output.textContent = input.value);
});
