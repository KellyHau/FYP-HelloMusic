const contextMenu = document.getElementById('context-menu');
let selectedSheetId = null;
let selectedTitle = null;
let user_role = null;

// Attach event listener to all elements with the 'music-sheet-item' class
document.querySelectorAll('.music-sheet-item').forEach(item => {
    item.addEventListener('contextmenu', function (event) {
        event.preventDefault(); // Prevent the default context menu

        // Get the selected music sheet's ID
        selectedSheetId = item.getAttribute('sheet-id');
        selectedTitle = item.querySelector('.sheet-title').textContent;

        document.getElementById('sheet-name').textContent = selectedTitle;

        fetch(`/shareSheet/${selectedSheetId}/`)
            .then(response => response.json())
            .then(data => {

                const userListContainer = document.getElementById('user_with_sheet');
                userListContainer.innerHTML = '';
                user_role = data.current_role;
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

    const deleteModal = new bootstrap.Modal(document.getElementById('deleteSheetModal'));
    deleteModal.show();


    document.getElementById('confirmDeleteSheet').addEventListener('click', function () {

        $.ajax({
            url: `/deleteSheet/${selectedSheetId}/`,
            type: 'POST',
            success: function (data) {
                deleteModal.hide();
                if (data.status) {
                    triggerAction('success', `${data.mes}`);
                } else {
                    showAlert('warning', `Failed to delete music sheet : ${data.mes}`);
                }
            },
            error: function (xhr, status, error) {
                showAlert('danger', 'An error occurred while deleting the music sheet.');
                console.error("Error in AJAX request:", error);
            }
        });
    });

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
        url: `/renameSheet/${currentSheetId}/`,
        type: 'POST',
        data: {
            'title': newTitle,
        },
        success: function (response) {
            $('#editTitleModal').modal('hide');
            if (response.status) { 
                const sheetItem = $(`.music-sheet-item[sheet-id=${currentSheetId}]`);
              
                sheetItem.find('.sheet-title').text(newTitle);
        
                sheetItem.find('.sheet-url').attr('href', `/sheet/${encodeURIComponent(newTitle)}/`);
        
                triggerAction('success', `${response.mes}`);
            } else {
                showAlert('warning', `Failed to edit music sheet : ${response.mes}`);
            }
        },
        error: function (xhr, status, error) {
            showAlert('danger', 'An error occurred while edit the music sheet.');
            console.error("Error in AJAX request:", error);
        }
    });
}


//open share window
document.getElementById('share-option').addEventListener('click', function (event) {
    event.preventDefault();

    currentSheetId = selectedSheetId;
    document.getElementById('shareSheetModalLabel').textContent = `Share "${selectedTitle}"`;
    contextMenu.style.display = 'none';

    if (user_role === "Viewer" || user_role === "viewer") {
        $('#user_role').hide();
    } else {
        $('#user_role').show();
    }

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
            $('#shareSheetModal').modal('hide');
            if (response.status) {
                $("#shareSheetForm")[0].reset();
                showAlert('success', `${response.mes}`);
            } else {
                showAlert('warning', `Failed to share music sheet : ${response.mes}`);
            }
        },
        error: function (xhr, status, error) {
            showAlert('danger', 'An error occurred while share the music sheet.');
            console.error("Error in AJAX request:", error);
        }
    });
}