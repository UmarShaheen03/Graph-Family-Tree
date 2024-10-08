document.addEventListener('DOMContentLoaded', function() {
    // Handle the 'Request Access to a Family Tree' form submission
    document.getElementById('requestTreeAccessForm').addEventListener('submit', function(event) {
        event.preventDefault();

        // Get the selected Family Tree ID
        const treeId = document.getElementById('tree_id').value;

        // Get the user's message (optional)
        const message = document.getElementById('message').value;

        // Check if the user has selected a family tree
        if (!treeId) {
            alert('Please select a Family Tree.');
            return;
        }
        
        // Show a confirmation alert with the tree and message
        alert('Tree Access Requested for: ' + treeId + '\nMessage: ' + (message ? message : 'No message provided'));

        // Placeholder for backend integration 
    });

    // Handle the 'Request Admin Access' form submission
    document.getElementById('requestAdminAccessForm').addEventListener('submit', function(event) {
        event.preventDefault();


        // Get the reason for requesting admin access
        const reason = document.getElementById('reason').value;

        // Check if a Family Tree ID and reason are provided
        if (!reason) {
            alert('Please select a Family Tree and provide a reason for admin access.');
            return;
        }

        // Show a confirmation alert
        alert('Admin Access Requested: ' + '\nReason: ' + reason);

        // Placeholder for backend integration 
    });

    // Handle the 'Enable Email Notifications' form submission
    document.getElementById('emailNotificationsForm').addEventListener('submit', function(event) {
        event.preventDefault();

        // Check if the email notifications checkbox is checked
        const emailEnabled = document.getElementById('email_notifications').checked;

        // Show an alert for email notification status
        alert('Email Notifications ' + (emailEnabled ? 'Enabled' : 'Disabled'));

        // Placeholder for backend integration
    });
});
