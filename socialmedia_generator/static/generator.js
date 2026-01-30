// UI Elements
const formSection = document.getElementById('formSection');
const loadingSection = document.getElementById('loadingSection');
const resultsSection = document.getElementById('resultsSection');
const errorSection = document.getElementById('errorSection');

// Form Elements
const dataSourcesContainer = document.getElementById('dataSourcesContainer');
const addDataSourceBtn = document.getElementById('addDataSourceBtn');
const languageTone = document.getElementById('languageTone');
const mediaImage = document.getElementById('mediaImage');
const mediaVideo = document.getElementById('mediaVideo');
const textVariations = document.getElementById('textVariations');
const mediaVariations = document.getElementById('mediaVariations');
const textVariationsValue = document.getElementById('textVariationsValue');
const mediaVariationsValue = document.getElementById('mediaVariationsValue');
const createBtn = document.getElementById('createBtn');

// Loading Elements
const updatesList = document.getElementById('updatesList');

// Results Elements
const textVariationsContainer = document.getElementById('textVariationsContainer');
const mediaVariationsContainer = document.getElementById('mediaVariationsContainer');
const regenerateBtn = document.getElementById('regenerateBtn');
const createPostBtn = document.getElementById('createPostBtn');
const backBtn = document.getElementById('backBtn');
const errorBackBtn = document.getElementById('errorBackBtn');
const errorMessage = document.getElementById('errorMessage');

// State
let currentPostId = null;
let currentData = null;
let selectedTextVariationId = null;
let selectedMediaVariationId = null;

// Initialize with one data source row
addDataSourceRow();

// Update slider values
textVariations.addEventListener('input', (e) => {
    textVariationsValue.textContent = e.target.value;
});

mediaVariations.addEventListener('input', (e) => {
    mediaVariationsValue.textContent = e.target.value;
});

// Data sources controls
addDataSourceBtn.addEventListener('click', () => addDataSourceRow());

function addDataSourceRow(type = 'link', content = '') {
    const row = document.createElement('div');
    row.className = 'source-row';

    row.innerHTML = `
        <div class="source-left">
            <div class="form-group">
                <label>Source Type:</label>
                <select class="source-type">
                    <option value="link">Link</option>
                    <option value="text">Text</option>
                </select>
            </div>
            <div class="form-group">
                <label>Content:</label>
                <textarea class="source-content" placeholder="Paste your link or text here..."></textarea>
            </div>
        </div>
        <div class="source-right">
            <div class="source-number"></div>
            <button type="button" class="btn btn-secondary btn-small remove-source-btn">Delete</button>
        </div>
    `;

    row.querySelector('.source-type').value = type;
    row.querySelector('.source-content').value = content;

    row.querySelector('.remove-source-btn').addEventListener('click', () => {
        const rows = dataSourcesContainer.querySelectorAll('.source-row');
        if (rows.length === 1) {
            alert('At least one data source is required.');
            return;
        }
        row.remove();
        updateSourceNumbers();
    });

    dataSourcesContainer.appendChild(row);
    updateSourceNumbers();
}

function updateSourceNumbers() {
    const rows = dataSourcesContainer.querySelectorAll('.source-row');
    rows.forEach((row, index) => {
        const numberLabel = row.querySelector('.source-number');
        if (numberLabel) {
            numberLabel.textContent = `Source #${index + 1}`;
        }
    });

    const removeButtons = dataSourcesContainer.querySelectorAll('.remove-source-btn');
    removeButtons.forEach((btn) => {
        if (rows.length === 1) {
            btn.setAttribute('disabled', 'disabled');
            btn.style.opacity = '0.6';
            btn.style.cursor = 'not-allowed';
        } else {
            btn.removeAttribute('disabled');
            btn.style.opacity = '1';
            btn.style.cursor = 'pointer';
        }
    });
}

function getDataSourcesFromUI() {
    const rows = dataSourcesContainer.querySelectorAll('.source-row');
    return Array.from(rows).map((row) => {
        const type = row.querySelector('.source-type')?.value || 'link';
        const content = row.querySelector('.source-content')?.value || '';
        return { type, content };
    });
}

// Create Post Button Click
createBtn.addEventListener('click', createPost);
regenerateBtn.addEventListener('click', regenerate);
createPostBtn.addEventListener('click', submitPost);
backBtn.addEventListener('click', goBack);
errorBackBtn.addEventListener('click', goBack);

async function createPost() {
    const sources = getDataSourcesFromUI();
    if (sources.length === 0) {
        alert('Please add at least one data source');
        return;
    }

    const hasEmpty = sources.some((s) => !s.content.trim());
    if (hasEmpty) {
        alert('Please fill content for all data sources');
        return;
    }

    if (!languageTone.value.trim()) {
        alert('Please describe the language and tone');
        return;
    }

    if (!mediaImage.checked && !mediaVideo.checked) {
        alert('Please select at least one media type');
        return;
    }

    // Prepare request data
    const mediaContent = [];
    if (mediaImage.checked) mediaContent.push('image');
    if (mediaVideo.checked) mediaContent.push('video');

    const contentTypeRadio = document.querySelector('input[name="contentType"]:checked');
    const contentType = contentTypeRadio ? contentTypeRadio.value : 'LongForm';

    const requestData = {
        data_sources: sources,
        language_tone: languageTone.value,
        media_content_needed: mediaContent.join(','),
        content_type: contentType,
        text_variations_count: parseInt(textVariations.value),
        media_variations_count: parseInt(mediaVariations.value)
    };

    try {
        // Show loading section
        formSection.classList.add('hidden');
        loadingSection.classList.remove('hidden');
        updatesList.innerHTML = '<div class="update-item">Sending request to server...</div>';

        // Make POST request
        const response = await fetch('http://localhost:8000/api/posts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        currentPostId = result.post_id;
        currentData = null;

        // Add update
        addUpdate(`Post created with ID: ${result.post_id}`);
        addUpdate('Connecting to WebSocket...');

        // Connect to WebSocket
        connectWebSocket(result.websocket_url);
    } catch (error) {
        showError(`Failed to create post: ${error.message}`);
    }
}

function connectWebSocket(wsPath) {
    const wsUrl = `ws://localhost:8000${wsPath}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        addUpdate('✓ Connected to live updates');
    };

    ws.onmessage = (event) => {
        try {
            const message = JSON.parse(event.data);
            
            if (message.type === 'complete') {
                handleComplete(message);
                ws.close();
            } else if (message.type === 'error') {
                handleWebSocketError(message);
                ws.close();
            } else {
                // Handle progress messages
                addUpdate(`${message.type}: ${message.message || 'Processing...'}`);
            }
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
            addUpdate(`Error: ${error.message}`);
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        showError('WebSocket connection error. Please try again.');
    };

    ws.onclose = () => {
        console.log('WebSocket closed');
    };
}

function addUpdate(message) {
    const updateItem = document.createElement('div');
    updateItem.className = 'update-item';
    updateItem.textContent = `• ${message}`;
    updatesList.appendChild(updateItem);
    updatesList.scrollTop = updatesList.scrollHeight;
}

function handleComplete(data) {
    currentData = data;

    // Populate text variations
    textVariationsContainer.innerHTML = '';
    if (data.text_variation_ids && data.text_variation_ids.length > 0) {
        data.text_variation_ids.forEach((variation, index) => {
            const card = createTextVariationCard(variation, index);
            textVariationsContainer.appendChild(card);
        });
        // Select first by default
        if (data.text_variation_ids.length > 0) {
            selectedTextVariationId = data.text_variation_ids[0].id;
            document.querySelector('[data-text-id="' + selectedTextVariationId + '"]')?.classList.add('selected');
        }
    }

    // Populate media variations
    mediaVariationsContainer.innerHTML = '';
    if (data.media_content_ids && data.media_content_ids.length > 0) {
        data.media_content_ids.forEach((variation, index) => {
            const card = createMediaVariationCard(variation, index);
            mediaVariationsContainer.appendChild(card);
        });
        // Select first by default
        if (data.media_content_ids.length > 0) {
            selectedMediaVariationId = data.media_content_ids[0].id;
            document.querySelector('[data-media-id="' + selectedMediaVariationId + '"]')?.classList.add('selected');
        }
    }

    // Show results section
    loadingSection.classList.add('hidden');
    resultsSection.classList.remove('hidden');
}

function handleWebSocketError(message) {
    showError(`Error during processing: ${message.message}`);
}

function createTextVariationCard(variation, index) {
    const card = document.createElement('div');
    card.className = 'variation-card';
    card.setAttribute('data-text-id', variation.id);
    card.innerHTML = `
        <div class="content">
            <div class="label">Variation #${variation.variation_number}</div>
            <div class="text">${variation.text_content}</div>
        </div>
    `;
    
    card.addEventListener('click', () => {
        document.querySelectorAll('#textVariationsContainer .variation-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        selectedTextVariationId = variation.id;
    });

    return card;
}

function createMediaVariationCard(variation, index) {
    const card = document.createElement('div');
    card.className = 'variation-card';
    card.setAttribute('data-media-id', variation.id);
    
    if (variation.media_type === 'image') {
        card.innerHTML = `
            <img src="${variation.file_path}" alt="Media variation ${variation.variation_number}" />
            <div class="content">
                <div class="label">Variation #${variation.variation_number} - Image</div>
                <div class="text">${variation.generation_prompt}</div>
            </div>
        `;
    } else {
        card.innerHTML = `
            <div class="content">
                <div class="label">Variation #${variation.variation_number} - ${variation.media_type.toUpperCase()}</div>
                <div class="text">${variation.generation_prompt}</div>
            </div>
        `;
    }
    
    card.addEventListener('click', () => {
        document.querySelectorAll('#mediaVariationsContainer .variation-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        selectedMediaVariationId = variation.id;
    });

    return card;
}

function regenerate() {
    if (!currentPostId) return;

    addUpdate('Regenerating content...');
    loadingSection.classList.remove('hidden');
    resultsSection.classList.add('hidden');
    updatesList.innerHTML = '<div class="update-item">Reconnecting to WebSocket...</div>';

    const wsPath = `/api/posts/${currentPostId}/updates`;
    connectWebSocket(wsPath);
}

function submitPost() {
    if (!selectedTextVariationId || !selectedMediaVariationId) {
        alert('Please select both a text and media variation');
        return;
    }

    // Here you would send the final post creation request
    const postData = {
        post_id: currentPostId,
        text_variation_id: selectedTextVariationId,
        media_variation_id: selectedMediaVariationId
    };

    console.log('Submitting post:', postData);
    alert('Post created successfully! (This would be sent to the actual endpoint)');
}

function goBack() {
    formSection.classList.remove('hidden');
    loadingSection.classList.add('hidden');
    resultsSection.classList.add('hidden');
    errorSection.classList.add('hidden');
    
    // Reset form
    dataSourcesContainer.innerHTML = '';
    addDataSourceRow();
    languageTone.value = '';
    textVariations.value = '1';
    mediaVariations.value = '1';
    textVariationsValue.textContent = '1';
    mediaVariationsValue.textContent = '1';
    mediaImage.checked = true;
    mediaVideo.checked = false;
    
    currentPostId = null;
    currentData = null;
    selectedTextVariationId = null;
    selectedMediaVariationId = null;
}

function showError(message) {
    errorMessage.textContent = message;
    loadingSection.classList.add('hidden');
    formSection.classList.add('hidden');
    resultsSection.classList.add('hidden');
    errorSection.classList.remove('hidden');
}
