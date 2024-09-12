document.addEventListener('DOMContentLoaded', function () {
    const actionField = document.querySelector('select[name="action"]');
    const nameGroup = document.getElementById('name-group');
    const newNameGroup = document.getElementById('new-name-group');
    const oldNameGroup = document.getElementById('old-name-group');
    const parentGroup = document.getElementById('parent-group');
    const newParentGroup = document.getElementById('new-parent-group');
    const personToShiftGroup = document.getElementById('person-to-shift-group');
    const personToDeleteGroup = document.getElementById('person-to-delete-group');

    function toggleFields() {
        const action = actionField.value;

        nameGroup.style.display = 'none';
        newNameGroup.style.display = 'none';
        oldNameGroup.style.display = 'none';
        parentGroup.style.display = 'none';
        newParentGroup.style.display = 'none';
        personToShiftGroup.style.display = 'none';
        personToDeleteGroup.style.display = 'none';

        if (action === 'add') {
            nameGroup.style.display = 'block';
            parentGroup.style.display = 'block';
        } else if (action === 'edit') {
            oldNameGroup.style.display = 'block';
            newNameGroup.style.display = 'block';
        } else if (action === 'delete') {
            personToDeleteGroup.style.display = 'block';
        } else if (action === 'shift') {
            personToShiftGroup.style.display = 'block';
            newParentGroup.style.display = 'block';
        }
    }

    // Initialize Select2 on all relevant select elements
    $('select.form-select-searchable').select2({
        theme:'bootstrap-5'
    });

    actionField.addEventListener('change', toggleFields);
    toggleFields();  // Initialize the form based on the current selection
});
