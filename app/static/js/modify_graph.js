document.addEventListener('DOMContentLoaded', function () {
    const actionField = document.querySelector('select[name="action"]');
    const nameGroup = document.getElementById('name-group');
    const oldNameGroup = document.getElementById('old-name-group');
    const parentGroup = document.getElementById('parent-group');
    const newParentGroup = document.getElementById('new-parent-group');

    function toggleFields() {
        const action = actionField.value;

        nameGroup.style.display = 'none';
        oldNameGroup.style.display = 'none';
        parentGroup.style.display = 'none';
        newParentGroup.style.display = 'none';

        if (action === 'add') {
            nameGroup.style.display = 'block';
            parentGroup.style.display = 'block';
        } else if (action === 'edit') {
            oldNameGroup.style.display = 'block';
            nameGroup.style.display = 'block';
        } else if (action === 'delete') {
            oldNameGroup.style.display = 'block';
        } else if (action === 'shift') {
            oldNameGroup.style.display = 'block';
            newParentGroup.style.display = 'block';
        }
    }

    actionField.addEventListener('change', toggleFields);
    toggleFields();  // Initialize the form based on the current selection
});
