// DocTrack main JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize drag and drop zones
    initDragDrop();
});

function initDragDrop() {
    document.querySelectorAll('.drag-drop-zone').forEach(zone => {
        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.classList.add('dragover');
        });
        zone.addEventListener('dragleave', () => {
            zone.classList.remove('dragover');
        });
        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('dragover');
            const input = zone.querySelector('input[type="file"]');
            if (input && e.dataTransfer.files.length) {
                input.files = e.dataTransfer.files;
                const event = new Event('change', { bubbles: true });
                input.dispatchEvent(event);
            }
        });
    });
}
