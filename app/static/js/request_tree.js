// request_tree.js

document.getElementById('requestTreeForm').addEventListener('submit', function(event) {
    event.preventDefault();  // Prevent default form submission for custom handling

    const treeName = document.getElementById('tree_name').value;
    const message = document.getElementById('request_message').value;

    if (treeName === '') {
        alert('Please enter a tree name.');
    } else {
        // For now, just alert the input values. In a real application, you would send this data to the server.
        alert('Request submitted for tree: ' + treeName + '\nMessage: ' + message);
        
        // Optionally, clear the form or close the modal
        document.getElementById('requestTreeForm').reset();
        document.querySelector('#requestTreeModal .btn-close').click();  // Close the modal
    }
});
