const contextMenu = document.getElementById('context-menu');
let selectedSheetId = null;
let selectedTitle = null;

// Attach event listener to all elements with the 'music-sheet-item' class
document.querySelectorAll('.music-sheet-item').forEach(item => {
    item.addEventListener('contextmenu', function (event) {
        event.preventDefault(); // Prevent the default context menu

        // Get the selected music sheet's ID
        selectedSheetId = item.getAttribute('sheet-id');
        selectedTitle = item.querySelector('.sheet-title').textContent;

        fetch(`/shareSheet/${selectedSheetId}/`)
            .then(response => response.json())
            .then(data => {

                const userListContainer = document.getElementById('user_with_sheet');
                userListContainer.innerHTML = ''; 
                data.users.forEach(user => {
                    const userItem = document.createElement('li');
                    userItem.textContent = `${user.email} (${user.role})`;
                    userListContainer.appendChild(userItem);
                });
            })
            .catch(error => console.error('Error fetching sheet details:', error));


        // Show the custom context menu at the mouse position
        contextMenu.style.display = 'block';
        contextMenu.style.left = `${event.pageX}px`;
        contextMenu.style.top = `${event.pageY}px`;
    });
});

// Hide context menu on left-click 
document.addEventListener('click', function (event) {
    if (!contextMenu.contains(event.target)) {
        contextMenu.style.display = 'none';
    }
});

// Hide the context menu if right-click 
document.addEventListener('contextmenu', function (event) {
    if (!event.target.closest('.music-sheet-item')) {
        contextMenu.style.display = 'none';
    }
});

//delete option click handler
$('#delete-option').on('click', function (event) {
    event.preventDefault();

    // Show confirmation dialog
    const confirmed = confirm("Are you sure you want to delete this music sheet?");

    if (confirmed && selectedSheetId) {
        // If confirmed, proceed to delete
        $.ajax({
            url: `/deleteSheet/${selectedSheetId}/`,
            type: 'POST',
            success: function (data) {
                if (data.success) {
                    alert("Music sheet deleted successfully.");
                    location.reload(); // Reload or update page as needed
                } else {
                    alert("Failed to delete music sheet: " + data.error);
                }
            },
            error: function (xhr, status, error) {
                console.error("Error in AJAX request:", error);
            }
        });
    }

    $('#context-menu').hide();
});


//open edit window
document.getElementById('edit-option').addEventListener('click', function (event) {
    event.preventDefault();

    currentSheetId = selectedSheetId;
    document.getElementById('newTitle').value = selectedTitle;
    contextMenu.style.display = 'none';
    $('#editTitleModal').modal('show');
});

//save sheet edit data
function saveTitle() {
    const newTitle = document.getElementById('newTitle').value;

    $.ajax({
        url: `/editSheet/${currentSheetId}/`,
        type: 'POST',
        data: {
            'title': newTitle,
        },
        success: function (response) {
            if (response.success) {
                // Update the title in the DOM without refreshing
                $(`.music-sheet-item[sheet-id=${currentSheetId}]`).find('.sheet-title').text(
                    newTitle);
                $('#editTitleModal').modal('hide');
            } else {
                alert(response.error);
            }
        },
        error: function () {
            alert('Error occurred while saving.');
        }
    });
}


//open share window
document.getElementById('share-option').addEventListener('click', function (event) {
    event.preventDefault();

    currentSheetId = selectedSheetId;
    document.getElementById('shareSheetModalLabel').textContent = `Share "${selectedTitle}"`;
    contextMenu.style.display = 'none';
    $('#shareSheetModal').modal('show');
});


//save share user permission
function savePermission() {
    const email = document.getElementById("email").value;
    const role = document.getElementById("role").value;

    $.ajax({
        url: `/shareSheet/${currentSheetId}/`,
        type: 'POST',
        data: {
            'email': email,
            'role': role,
        },
        success: function (response) {
            if (response.success) {
                $("#shareSheetForm")[0].reset();
                $('#shareSheetModal').modal('hide');
            } else {
                alert(response.error);
            }
        },
        error: function () {
            alert('Error occurred while saving.');
        }
    });
}