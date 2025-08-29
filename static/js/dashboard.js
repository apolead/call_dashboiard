/**
 * Dashboard JavaScript for Audio Transcription System
 * Handles real-time updates, user interactions, and data management
 */

class AudioTranscriptionDashboard {
    constructor() {
        this.table = null;
        this.refreshInterval = null;
        this.currentRefreshRate = 0; // disabled
        this.isLoading = false;
        this.currentFilename = null;
        
        this.init();
    }
    
    init() {
        // Initialize components when DOM is ready
        $(document).ready(() => {
            this.initializeDataTable();
            this.setupEventListeners();
            this.setupThemeToggle();
            this.loadInitialData();
            this.startAutoRefresh();
            this.checkHealth();
        });
    }
    
    initializeDataTable() {
        console.log('Initializing DataTable...');
        const tableElement = $('#transcriptionTable');
        
        if (tableElement.length === 0) {
            console.error('Table element #transcriptionTable not found!');
            return;
        }
        
        console.log('Table element found, initializing DataTable...');
        
        try {
            this.table = tableElement.DataTable({
                responsive: true,
                pageLength: 20,
                order: [[0, 'desc']], // Sort by timestamp descending
                columnDefs: [
                    {
                        targets: 0, // Timestamp column
                        render: (data) => this.formatTimestamp(data)
                    },
                    {
                        targets: 2, // File size column
                        render: (data) => data
                    },
                    {
                        targets: 3, // Duration column
                        render: (data) => data
                    },
                    {
                        targets: 4, // Intent column
                        render: (data) => this.renderIntentBadge(data)
                    },
                    {
                        targets: 5, // Sub-Intent column
                        render: (data) => this.renderSubIntentBadge(data)
                    },
                    {
                        targets: 6, // Primary Disposition column
                        render: (data) => this.renderDispositionBadge(data, 'primary')
                    },
                    {
                        targets: 7, // Secondary Disposition column
                        render: (data) => this.renderDispositionBadge(data, 'secondary')
                    },
                    {
                        targets: 8, // Summary column
                        render: (data, type, row) => this.renderSummaryColumn(data, row)
                    },
                    {
                        targets: 9, // Status column
                        render: (data) => this.renderStatusBadge(data)
                    },
                    {
                        targets: 11, // Actions column
                        orderable: false,
                        render: (data, type, row) => this.renderActionButtons(row)
                    }
                ],
                language: {
                    emptyTable: "No transcription records found",
                    zeroRecords: "No matching records found",
                    info: "Showing _START_ to _END_ of _TOTAL_ entries",
                    infoEmpty: "Showing 0 to 0 of 0 entries",
                    infoFiltered: "(filtered from _MAX_ total entries)",
                    search: "Search:",
                    paginate: {
                        first: "First",
                        last: "Last",
                        next: "Next",
                        previous: "Previous"
                    }
                }
            });
            
            console.log('DataTable initialized successfully');
            
        } catch (error) {
            console.error('Error initializing DataTable:', error);
        }
    }
    
    setupEventListeners() {
        // Refresh button
        $('#refreshBtn').on('click', () => this.refreshData());
        
        // Auto-refresh interval selection
        $('.dropdown-menu a[data-interval]').on('click', (e) => {
            e.preventDefault();
            const interval = parseInt($(e.target).data('interval'));
            this.setRefreshInterval(interval);
            
            // Update active state
            $('.dropdown-menu a').removeClass('active');
            $(e.target).addClass('active');
        });
        
        // Search functionality
        $('#searchInput').on('keyup', (e) => {
            const query = $(e.target).val();
            if (e.key === 'Enter' || query.length === 0 || query.length >= 3) {
                this.performSearch(query);
            }
        });
        
        $('#clearSearch').on('click', () => {
            $('#searchInput').val('');
            this.loadData();
        });
        
        // Status filter
        $('#statusFilter').on('change', (e) => {
            const status = $(e.target).val();
            this.filterByStatus(status);
        });
        
        // Intent filter
        $('#intentFilter').on('change', (e) => {
            const intent = $(e.target).val();
            this.filterByIntent(intent);
        });
        
        // Sub-Intent filter
        $('#subIntentFilter').on('change', (e) => {
            const subIntent = $(e.target).val();
            this.filterBySubIntent(subIntent);
        });
        
        // Duration filter
        $('#durationFilter').on('change', (e) => {
            const duration = $(e.target).val();
            this.filterByDuration(duration);
        });
        
        $('#primaryDispositionFilter').on('change', (e) => {
            const disposition = $(e.target).val();
            this.filterByPrimaryDisposition(disposition);
        });
        
        $('#secondaryDispositionFilter').on('change', (e) => {
            const disposition = $(e.target).val();
            this.filterBySecondaryDisposition(disposition);
        });
        
        // Export functionality
        $('#exportCsv').on('click', () => this.exportData('csv'));
        $('#exportJson').on('click', () => this.exportData('json'));
        
        // Upload functionality
        $('#uploadBtn').on('click', () => this.handleFileUpload());
        $('#audioFile').on('change', () => this.validateFileUpload());
        
        // Modal event handlers
        $('#detailsModal').on('hidden.bs.modal', () => this.currentFilename = null);
        $('#reprocessBtn').on('click', () => this.reprocessFile());
        $('#deleteBtn').on('click', () => this.showDeleteConfirmation());
        $('#confirmBtn').on('click', () => this.executeConfirmedAction());
        
        // S3 functionality
        $('#s3SyncBtn').on('click', () => this.syncFromS3());
        $('#s3Modal').on('shown.bs.modal', () => this.loadS3Recordings());
        $('#refreshS3').on('click', () => this.loadS3Recordings());
        $('#s3TimeFilter').on('change', () => this.loadS3Recordings());
        $('#downloadAllBtn').on('click', () => this.downloadAllNewRecordings());
        
        // Transcript button event delegation (for dynamically created buttons)
        $(document).on('click', '.btn-transcript', (e) => {
            e.preventDefault();
            const filename = $(e.currentTarget).data('filename');
            console.log('Transcript button clicked for filename:', filename);
            this.showTranscriptModal(filename);
        });
        
        // Chart refresh buttons
        $('#subIntentChartRefresh').on('click', () => this.loadSubIntentDistribution());
        $('#durationChartRefresh').on('click', () => this.loadDurationDistribution());
        $('#speakerChartRefresh').on('click', () => this.loadSpeakerDistribution());
        $('#dropoffChartRefresh').on('click', () => this.loadDropOffAnalysis());
        $('#intentSubIntentBreakdownRefresh').on('click', () => this.loadIntentSubIntentBreakdown());
        $('#primaryDispositionChartRefresh').on('click', () => this.loadDispositionDistribution());
        $('#secondaryDispositionChartRefresh').on('click', () => this.loadDispositionDistribution());
        $('#classifyDispositionsBtn').on('click', () => this.classifyDispositions());
        
        // Analytics section collapse/expand
        $('#analyticsSection').on('shown.bs.collapse', () => {
            $('#analyticsToggleIcon').removeClass('bi-chevron-down').addClass('bi-chevron-up');
            $('#analyticsToggleText').text('Collapse');
        });
        $('#analyticsSection').on('hidden.bs.collapse', () => {
            $('#analyticsToggleIcon').removeClass('bi-chevron-up').addClass('bi-chevron-down');
            $('#analyticsToggleText').text('Expand');
        });
        
        // Transcription view toggle
        $('input[name="transcriptionView"]').on('change', function() {
            if ($(this).attr('id') === 'regularTranscript') {
                $('#regularTranscriptionView').show();
                $('#diarizedTranscriptionView').hide();
            } else {
                $('#regularTranscriptionView').hide();
                $('#diarizedTranscriptionView').show();
            }
        });
    }
    
    setupThemeToggle() {
        const themeToggle = document.getElementById('themeToggle');
        const themeIcon = document.getElementById('themeIcon');
        const currentTheme = localStorage.getItem('theme') || 'light';
        
        // Set initial theme
        document.documentElement.setAttribute('data-bs-theme', currentTheme);
        this.updateThemeIcon(currentTheme);
        
        themeToggle.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            this.updateThemeIcon(newTheme);
        });
    }
    
    updateThemeIcon(theme) {
        const themeIcon = document.getElementById('themeIcon');
        themeIcon.className = theme === 'dark' ? 'bi bi-moon-fill' : 'bi bi-sun-fill';
    }
    
    loadInitialData() {
        this.loadData();
        this.loadStats();
        this.loadAnalytics();
    }
    
    async loadData() {
        if (this.isLoading) return;
        
        console.log('Loading data...');
        this.isLoading = true;
        this.showLoading();
        
        try {
            console.log('Making API call to /api/data');
            console.log('Current URL:', window.location.href);
            console.log('API URL will be:', window.location.origin + '/api/data');
            
            // Use fetch instead of jQuery to have better control over response parsing
            const fetchResponse = await fetch('/api/data');
            console.log('Fetch response status:', fetchResponse.status);
            console.log('Fetch response ok:', fetchResponse.ok);
            
            if (!fetchResponse.ok) {
                throw new Error(`HTTP ${fetchResponse.status}: ${fetchResponse.statusText}`);
            }
            
            const response = await fetchResponse.json();
            console.log('API response received:', response);
            console.log('Response type:', typeof response);
            console.log('Response keys:', Object.keys(response || {}));
            console.log('Data exists:', !!response.data);
            console.log('Data is array:', Array.isArray(response.data));
            console.log('Data length:', response.data ? response.data.length : 'No data');
            
            if (response.data && Array.isArray(response.data)) {
                console.log('First record:', response.data[0]);
            }
            
            this.updateTable(response.data);
            this.updateRecordCount(response.total);
            this.updateLastUpdate();
            console.log('Data loading completed successfully');
        } catch (error) {
            console.error('Error loading data:', error);
            console.error('Error details:', error.message || error.responseText);
            console.error('Error status:', error.status);
            console.log('Full error object:', error);
            
            // Handle jQuery error with status 200 (common jQuery issue with content-type)
            if (error.status === 200) {
                console.log('Status 200 error - likely jQuery content-type issue');
                
                // Try different ways to get the response data
                let responseData = null;
                
                if (error.responseText) {
                    try {
                        responseData = JSON.parse(error.responseText);
                        console.log('Parsed from responseText:', responseData);
                    } catch (parseError) {
                        console.error('Could not parse responseText:', parseError);
                    }
                }
                
                if (!responseData && error.responseJSON) {
                    responseData = error.responseJSON;
                    console.log('Using responseJSON:', responseData);
                }
                
                if (!responseData && typeof error === 'object' && error.data) {
                    responseData = error;
                    console.log('Using error object directly:', responseData);
                }
                
                if (responseData && responseData.data && Array.isArray(responseData.data)) {
                    console.log('Found valid data, populating table...');
                    this.updateTable(responseData.data);
                    this.updateRecordCount(responseData.total || responseData.data.length);
                    this.updateLastUpdate();
                    return; // Exit successfully
                }
            }
            
            this.showError('Failed to load data: ' + (error.message || 'Unknown error'));
        } finally {
            this.isLoading = false;
            this.hideLoading();
        }
    }
    
    async loadStats() {
        try {
            const response = await $.get('/api/stats');
            this.updateStats(response);
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }
    
    updateTable(data) {
        console.log('=== UPDATE TABLE CALLED ===');
        console.log('Data received:', data);
        console.log('Data type:', typeof data);
        console.log('Data is array:', Array.isArray(data));
        
        if (!this.table) {
            console.error('Table not initialized!');
            console.error('this.table is:', this.table);
            return;
        }
        
        console.log('Table exists:', !!this.table);
        console.log('Table info:', this.table.settings());
        
        if (!data || !Array.isArray(data)) {
            console.error('Invalid data for table - not array or null:', data);
            console.log('Setting empty message...');
            this.table.clear().draw();
            return;
        }
        
        console.log('Valid data received, length:', data.length);
        
        // Clear existing data
        console.log('Clearing existing table data...');
        this.table.clear();
        
        if (data.length === 0) {
            console.log('No data to add, drawing empty table...');
            this.table.draw();
            return;
        }
        
        console.log('Adding', data.length, 'rows to table...');
        // Add new data
        data.forEach((row, index) => {
            console.log(`Processing row ${index + 1}:`, row);
            console.log('Row keys:', Object.keys(row));
            
            const tableRow = [
                row.timestamp,
                row.filename,
                row.file_size,
                row.duration,
                row.intent,
                row.sub_intent || 'GENERAL_INQUIRY',
                row.primary_disposition || '',
                row.secondary_disposition || '',
                row.summary || '',
                row.status,
                row.processing_time,
                '' // Actions column will be rendered by columnDefs
            ];
            
            console.log(`Adding table row ${index + 1}:`, tableRow);
            try {
                this.table.row.add(tableRow);
                console.log(`Successfully added row ${index + 1}`);
            } catch (error) {
                console.error(`Error adding row ${index + 1}:`, error);
            }
        });
        
        console.log('Redrawing table...');
        try {
            this.table.draw();
            console.log('Table redraw completed successfully');
            console.log('Final table row count:', this.table.rows().count());
        } catch (error) {
            console.error('Error during table draw:', error);
        }
        
        console.log('=== TABLE UPDATE COMPLETED ===');
    }
    
    updateStats(stats) {
        console.log('Updating stats:', stats);
        $('#totalCalls').text(stats.total_files || stats.total || 0);
        $('#successRate').text(`${stats.success_rate || 0}%`);
        $('#avgProcessingTime').text(`${stats.avg_processing_time || 0}s`);
        $('#totalDuration').text(this.formatDuration(stats.total_duration || 0));
    }
    
    updateRecordCount(count) {
        $('#recordCount').text(count);
    }
    
    updateLastUpdate() {
        const now = new Date();
        $('#lastUpdate').text(now.toLocaleTimeString());
    }
    
    renderStatusBadge(status) {
        const badges = {
            'completed': '<span class="badge bg-success">Completed</span>',
            'failed': '<span class="badge bg-danger">Failed</span>',
            'processing': '<span class="badge bg-warning">Processing</span>'
        };
        return badges[status] || `<span class="badge bg-secondary">${status}</span>`;
    }
    
    renderIntentBadge(intent) {
        const intentColors = {
            'ROOFING': 'bg-primary',
            'WINDOWS_DOORS': 'bg-info',
            'PLUMBING': 'bg-secondary',
            'ELECTRICAL': 'bg-warning',
            'HVAC': 'bg-success',
            'FLOORING': 'bg-dark',
            'SIDING_EXTERIOR': 'bg-primary',
            'KITCHEN_BATH': 'bg-info',
            'GENERAL_CONTRACTOR': 'bg-secondary',
            'EMERGENCY_REPAIR': 'bg-danger',
            'QUOTE_REQUEST': 'bg-success',
            'COMPLAINT': 'bg-danger',
            'OTHER': 'bg-light text-dark'
        };
        
        const color = intentColors[intent] || 'bg-secondary';
        const displayName = intent ? intent.replace(/_/g, ' ') : 'OTHER';
        return `<span class="badge ${color} text-capitalize">${displayName.toLowerCase()}</span>`;
    }
    
    renderSubIntentBadge(subIntent) {
        const subIntentColors = {
            'GENERAL_INQUIRY': 'bg-info',
            'PRODUCT_SPECIFIC': 'bg-primary',
            'PRICING_REQUEST': 'bg-warning',
            'AVAILABILITY_CHECK': 'bg-success',
            'TECHNICAL_SUPPORT': 'bg-danger',
            'COMPLAINT_RESOLUTION': 'bg-dark',
            'FOLLOW_UP': 'bg-secondary',
            'APPOINTMENT_REQUEST': 'bg-primary',
            'WARRANTY_INQUIRY': 'bg-info',
            'OTHER': 'bg-light text-dark'
        };
        
        const color = subIntentColors[subIntent] || 'bg-info';
        const displayName = subIntent ? subIntent.replace(/_/g, ' ') : 'GENERAL INQUIRY';
        return `<span class="badge ${color} text-capitalize" style="font-size: 0.75em;">${displayName.toLowerCase()}</span>`;
    }
    
    renderDispositionBadge(disposition, type) {
        if (!disposition || disposition === '') {
            return '<span class="text-muted">-</span>';
        }
        
        const primaryColors = {
            'APPOINTMENT_SET': 'bg-success',
            'QUALIFIED_LEAD': 'bg-primary',
            'NOT_QUALIFIED': 'bg-warning',
            'NOT_INTERESTED': 'bg-danger',
            'CALLBACK_REQUESTED': 'bg-info',
            'WRONG_NUMBER': 'bg-secondary',
            'NO_ANSWER': 'bg-light text-dark',
            'HANG_UP': 'bg-dark',
            'VOICEMAIL': 'bg-info',
            'TECHNICAL_ISSUE': 'bg-warning',
            'OTHER': 'bg-secondary'
        };
        
        const secondaryColors = {
            'IMMEDIATE': 'bg-success',
            'FUTURE': 'bg-primary',
            'PRICE_OBJECTION': 'bg-warning',
            'TRUST_OBJECTION': 'bg-danger',
            'DECISION_MAKER': 'bg-info',
            'RESEARCH_NEEDED': 'bg-secondary',
            'COMPETITOR': 'bg-warning',
            'SEASONAL': 'bg-info',
            'BUDGET_CONSTRAINTS': 'bg-warning',
            'PROPERTY_ISSUE': 'bg-secondary',
            'REFERRAL_NEEDED': 'bg-primary',
            'FOLLOW_UP_REQUIRED': 'bg-info',
            'OTHER': 'bg-light text-dark'
        };
        
        const colors = type === 'primary' ? primaryColors : secondaryColors;
        const color = colors[disposition] || 'bg-secondary';
        const displayName = disposition.replace(/_/g, ' ');
        return `<span class="badge ${color} text-capitalize" style="font-size: 0.7em;">${displayName.toLowerCase()}</span>`;
    }
    
    renderSummaryColumn(summary, row) {
        if (!summary || summary.trim() === '') {
            return '<span class="text-muted">No summary</span>';
        }
        
        const escapedSummary = summary.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
        const filename = row[1]; // Filename is in column 1
        
        return `<button class="btn btn-sm btn-outline-primary" 
                       onclick="dashboard.showSummaryModal('${filename}', '${escapedSummary}')"
                       title="Click to view call summary">
                    <i class="bi bi-chat-text me-1"></i>View Summary
                </button>`;
    }
    
    renderActionButtons(row) {
        const filename = row[1]; // filename is in column 1
        return `
            <button class="btn btn-primary btn-sm btn-transcript" 
                    data-filename="${filename}"
                    title="View Full Transcript">
                <i class="bi bi-file-text me-1"></i>Transcript
            </button>
        `;
    }
    
    async showFileDetails(filename) {
        try {
            this.showLoading();
            const response = await $.get(`/api/file/${encodeURIComponent(filename)}`);
            this.populateDetailsModal(response);
            $('#detailsModal').modal('show');
        } catch (error) {
            console.error('Error loading file details:', error);
            this.showError('Failed to load file details');
        } finally {
            this.hideLoading();
        }
    }
    
    populateDetailsModal(data) {
        this.currentFilename = data.filename;
        
        $('#detailsTitle').text(`Details: ${data.filename}`);
        $('#detailFilename').text(data.filename);
        $('#detailSize').text(data.file_size);
        $('#detailDuration').text(data.duration);
        $('#detailStatus').html(this.renderStatusBadge(data.status));
        $('#detailProcessingTime').text(data.processing_time);
        $('#detailTimestamp').text(this.formatTimestamp(data.timestamp));
        $('#detailTranscription').text(data.transcription || 'No transcription available');
        
        // Handle diarized transcription
        const diarizedTranscription = data.diarized_transcription || '';
        if (diarizedTranscription) {
            this.renderDiarizedTranscription(diarizedTranscription);
        } else {
            $('#detailDiarizedTranscription').html('<p class="text-muted">No speaker-separated transcription available</p>');
        }
        
        $('#detailSummary').text(data.summary || 'No summary available');
        $('#detailIntent').html(this.renderIntentBadge(data.intent));
        $('#detailSubIntent').html(this.renderSubIntentBadge(data.sub_intent));
        
        // Show/hide error section
        if (data.error_message) {
            $('#detailError').removeClass('d-none');
            $('#detailErrorMessage').text(data.error_message);
        } else {
            $('#detailError').addClass('d-none');
        }
    }
    
    async performSearch(query) {
        if (!query) {
            this.loadData();
            return;
        }
        
        try {
            this.showLoading();
            const response = await $.get('/api/search', { q: query });
            this.updateTable(response.data);
            this.updateRecordCount(response.total);
        } catch (error) {
            console.error('Error performing search:', error);
            this.showError('Search failed');
        } finally {
            this.hideLoading();
        }
    }
    
    filterByStatus(status) {
        if (this.table) {
            this.table.column(7).search(status).draw(); // Status is now column 7
        }
    }
    
    filterByIntent(intent) {
        if (this.table) {
            this.table.column(4).search(intent).draw(); // Intent is column 4
        }
    }
    
    filterBySubIntent(subIntent) {
        if (this.table) {
            this.table.column(5).search(subIntent).draw(); // Sub-Intent is column 5
        }
    }
    
    filterByDuration(durationRange) {
        if (this.table) {
            // Remove previous duration filter if exists
            if (this.currentDurationFilter) {
                const index = $.fn.dataTable.ext.search.indexOf(this.currentDurationFilter);
                if (index > -1) {
                    $.fn.dataTable.ext.search.splice(index, 1);
                }
                this.currentDurationFilter = null;
            }
            
            if (durationRange) {
                // Add custom duration filter
                const durationFilter = (settings, data, dataIndex) => {
                    const durationText = data[3]; // Duration is column 3
                    
                    // Parse duration from text like "1m 23s" or "45s"
                    let totalSeconds = 0;
                    const durationMatch = durationText.match(/(?:(\d+)h\s*)?(?:(\d+)m\s*)?(?:(\d+)s)?/);
                    if (durationMatch) {
                        const hours = parseInt(durationMatch[1] || 0);
                        const minutes = parseInt(durationMatch[2] || 0);
                        const seconds = parseInt(durationMatch[3] || 0);
                        totalSeconds = hours * 3600 + minutes * 60 + seconds;
                    }
                    
                    // Apply filter based on duration range
                    switch(durationRange) {
                        case 'short':
                            return totalSeconds < 60;
                        case 'medium':
                            return totalSeconds < 120;
                        case 'long':
                            return totalSeconds >= 120;
                        default:
                            return true;
                    }
                };
                
                // Store reference to the filter function
                this.currentDurationFilter = durationFilter;
                $.fn.dataTable.ext.search.push(durationFilter);
            }
            
            this.table.draw();
        }
    }
    
    filterByPrimaryDisposition(disposition) {
        if (this.table) {
            this.table.column(6).search(disposition).draw(); // Primary disposition is column 6
        }
    }
    
    filterBySecondaryDisposition(disposition) {
        if (this.table) {
            this.table.column(7).search(disposition).draw(); // Secondary disposition is column 7
        }
    }
    
    async exportData(format) {
        try {
            const response = await fetch(`/api/export?format=${format}`);
            
            if (format === 'csv') {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `transcriptions_${new Date().toISOString().split('T')[0]}.csv`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                const data = await response.json();
                const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `transcriptions_${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            }
            
            this.showSuccess(`Data exported successfully as ${format.toUpperCase()}`);
        } catch (error) {
            console.error('Error exporting data:', error);
            this.showError('Export failed');
        }
    }
    
    validateFileUpload() {
        const fileInput = $('#audioFile')[0];
        const uploadBtn = $('#uploadBtn');
        const fileList = $('#fileList');
        const selectedFiles = $('#selectedFiles');
        
        if (fileInput.files.length === 0) {
            uploadBtn.prop('disabled', true);
            fileList.addClass('d-none');
            return;
        }
        
        const maxSize = 100 * 1024 * 1024; // 100MB
        const allowedTypes = ['audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/flac', 'audio/ogg'];
        
        let validFiles = 0;
        let fileListHtml = '';
        
        for (let i = 0; i < fileInput.files.length; i++) {
            const file = fileInput.files[i];
            let status = 'valid';
            let statusClass = 'text-success';
            let statusIcon = 'bi-check-circle';
            let statusText = 'Ready to upload';
            
            if (file.size > maxSize) {
                status = 'invalid';
                statusClass = 'text-danger';
                statusIcon = 'bi-exclamation-circle';
                statusText = 'File too large (max 100MB)';
            } else if (!allowedTypes.includes(file.type) && !file.name.match(/\.(mp3|wav|m4a|flac|ogg)$/i)) {
                status = 'invalid';
                statusClass = 'text-danger';
                statusIcon = 'bi-exclamation-circle';
                statusText = 'Unsupported format';
            } else {
                validFiles++;
            }
            
            fileListHtml += `
                <div class="d-flex justify-content-between align-items-center mb-2 p-2 border rounded">
                    <div>
                        <strong>${file.name}</strong><br>
                        <small class="text-muted">${this.formatFileSize(file.size)}</small>
                    </div>
                    <div class="text-end">
                        <i class="bi ${statusIcon} ${statusClass}"></i>
                        <small class="${statusClass}">${statusText}</small>
                    </div>
                </div>
            `;
        }
        
        selectedFiles.html(fileListHtml);
        fileList.removeClass('d-none');
        uploadBtn.prop('disabled', validFiles === 0);
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    async handleFileUpload() {
        const fileInput = $('#audioFile')[0];
        const progressBar = $('#uploadProgress .progress-bar');
        const uploadProgress = $('#uploadProgress');
        
        if (fileInput.files.length === 0) {
            this.showError('Please select files to upload');
            return;
        }
        
        const formData = new FormData();
        for (let i = 0; i < fileInput.files.length; i++) {
            formData.append('files', fileInput.files[i]);
        }
        
        try {
            uploadProgress.removeClass('d-none');
            progressBar.css('width', '0%');
            
            const response = await $.ajax({
                url: '/api/upload',
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                xhr: function() {
                    const xhr = new window.XMLHttpRequest();
                    xhr.upload.addEventListener('progress', function(evt) {
                        if (evt.lengthComputable) {
                            const percentComplete = (evt.loaded / evt.total) * 100;
                            progressBar.css('width', percentComplete + '%');
                        }
                    }, false);
                    return xhr;
                }
            });
            
            // Show detailed results
            let message = response.message;
            if (response.errors && response.errors.length > 0) {
                message += '<br><br><strong>Issues:</strong><br>' + response.errors.join('<br>');
            }
            
            if (response.uploaded_count > 0) {
                this.showSuccess(message);
            } else {
                this.showError(message);
            }
            
            $('#uploadModal').modal('hide');
            $('#audioFile').val('');
            $('#fileList').addClass('d-none');
            uploadProgress.addClass('d-none');
            
            // Refresh data after upload
            setTimeout(() => this.refreshData(), 2000);
            
        } catch (error) {
            console.error('Error uploading files:', error);
            this.showError('Upload failed: ' + (error.responseJSON?.error || 'Unknown error'));
            uploadProgress.addClass('d-none');
        }
    }
    
    async reprocessFile(filename = this.currentFilename) {
        if (!filename) return;
        
        try {
            this.showLoading();
            const response = await $.ajax({
                url: `/api/reprocess/${encodeURIComponent(filename)}`,
                type: 'POST'
            });
            
            this.showSuccess(response.message);
            this.refreshData();
            
            if ($('#detailsModal').hasClass('show')) {
                $('#detailsModal').modal('hide');
            }
            
        } catch (error) {
            console.error('Error reprocessing file:', error);
            this.showError('Reprocessing failed: ' + (error.responseJSON?.error || 'Unknown error'));
        } finally {
            this.hideLoading();
        }
    }
    
    showDeleteConfirmation(filename = this.currentFilename) {
        if (!filename) return;
        
        this.currentFilename = filename;
        $('#confirmTitle').text('Confirm Deletion');
        $('#confirmMessage').text(`Are you sure you want to delete the record for "${filename}"? This action cannot be undone.`);
        $('#confirmBtn').removeClass('btn-warning').addClass('btn-danger').text('Delete');
        $('#confirmModal').modal('show');
    }
    
    async executeConfirmedAction() {
        if (!this.currentFilename) return;
        
        try {
            this.showLoading();
            const response = await $.ajax({
                url: `/api/delete/${encodeURIComponent(this.currentFilename)}`,
                type: 'DELETE'
            });
            
            this.showSuccess(response.message);
            this.refreshData();
            
            $('#confirmModal').modal('hide');
            if ($('#detailsModal').hasClass('show')) {
                $('#detailsModal').modal('hide');
            }
            
        } catch (error) {
            console.error('Error deleting record:', error);
            this.showError('Deletion failed: ' + (error.responseJSON?.error || 'Unknown error'));
        } finally {
            this.hideLoading();
        }
    }
    
    refreshData() {
        this.loadData();
        this.loadStats();
    }
    
    setRefreshInterval(seconds) {
        this.currentRefreshRate = seconds;
        
        // Clear existing interval
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
        
        // Start new interval if not manual
        if (seconds > 0) {
            this.startAutoRefresh();
        }
    }
    
    startAutoRefresh() {
        if (this.currentRefreshRate > 0) {
            this.refreshInterval = setInterval(() => {
                if (!this.isLoading) {
                    this.refreshData();
                }
            }, this.currentRefreshRate * 1000);
        }
    }
    
    async checkHealth() {
        try {
            const response = await $.get('/api/health');
            this.updateHealthStatus(response);
        } catch (error) {
            console.error('Health check failed:', error);
            this.updateHealthStatus({ status: 'unhealthy' });
        }
        
        // Schedule next health check
        setTimeout(() => this.checkHealth(), 30000); // Check every 30 seconds
    }
    
    updateHealthStatus(health) {
        const statusBadge = $('#statusBadge');
        const statusText = $('#statusText');
        
        if (health.status === 'healthy') {
            statusBadge.removeClass('bg-danger bg-warning').addClass('bg-success');
            statusText.text('Connected');
        } else if (health.status === 'degraded') {
            statusBadge.removeClass('bg-success bg-danger').addClass('bg-warning');
            statusText.text('Degraded');
        } else {
            statusBadge.removeClass('bg-success bg-warning').addClass('bg-danger');
            statusText.text('Disconnected');
        }
    }
    
    // Utility methods
    formatTimestamp(timestamp) {
        return new Date(timestamp).toLocaleString();
    }
    
    formatDuration(seconds) {
        if (seconds === 0) return '0s';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}h ${minutes}m ${secs}s`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    }
    
    showLoading() {
        $('#loadingSpinner').addClass('show');
    }
    
    hideLoading() {
        $('#loadingSpinner').removeClass('show');
    }
    
    showSuccess(message) {
        this.showToast(message, 'success');
    }
    
    showError(message) {
        this.showToast(message, 'danger');
    }
    
    showToast(message, type = 'info') {
        const toast = $(`
            <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `);
        
        // Create toast container if it doesn't exist
        if ($('#toastContainer').length === 0) {
            $('body').append('<div id="toastContainer" class="toast-container position-fixed top-0 end-0 p-3"></div>');
        }
        
        $('#toastContainer').append(toast);
        const bsToast = new bootstrap.Toast(toast[0]);
        bsToast.show();
        
        // Remove toast element after it's hidden
        toast.on('hidden.bs.toast', function() {
            $(this).remove();
        });
    }
    
    // S3 Management Methods
    async syncFromS3() {
        try {
            this.showLoading();
            
            const response = await $.ajax({
                url: '/api/s3/sync',
                type: 'POST'
            });
            
            this.showSuccess(response.message);
            
            // Refresh main data if files were downloaded
            if (response.downloaded_count > 0) {
                setTimeout(() => this.refreshData(), 2000);
            }
            
        } catch (error) {
            console.error('Error syncing from S3:', error);
            this.showError('S3 sync failed: ' + (error.responseJSON?.error || 'Unknown error'));
        } finally {
            this.hideLoading();
        }
    }
    
    async loadS3Recordings() {
        try {
            $('#s3Loading').removeClass('d-none');
            $('#s3Error').addClass('d-none');
            
            const sinceHours = $('#s3TimeFilter').val();
            
            // Load recordings and stats in parallel
            const [recordingsResponse, statsResponse] = await Promise.all([
                $.get('/api/s3/recordings', { since_hours: sinceHours, limit: 100 }),
                $.get('/api/s3/stats')
            ]);
            
            this.updateS3Table(recordingsResponse.recordings);
            this.updateS3Stats(statsResponse);
            
        } catch (error) {
            console.error('Error loading S3 recordings:', error);
            $('#s3Error').removeClass('d-none');
        } finally {
            $('#s3Loading').addClass('d-none');
        }
    }
    
    updateS3Table(recordings) {
        const tbody = $('#s3RecordingsTable tbody');
        tbody.empty();
        
        if (recordings.length === 0) {
            tbody.append(`
                <tr>
                    <td colspan="4" class="text-center text-muted">
                        No recordings found in the selected time range
                    </td>
                </tr>
            `);
            return;
        }
        
        recordings.forEach(recording => {
            const row = $(`
                <tr>
                    <td>
                        <div class="d-flex align-items-center">
                            <i class="bi bi-file-earmark-music me-2 text-primary"></i>
                            <span>${recording.filename}</span>
                        </div>
                    </td>
                    <td>${recording.size}</td>
                    <td>${recording.last_modified_formatted}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary" 
                                onclick="dashboard.downloadS3Recording('${recording.key}', '${recording.filename}')"
                                title="Download this recording">
                            <i class="bi bi-download"></i>
                        </button>
                    </td>
                </tr>
            `);
            tbody.append(row);
        });
    }
    
    updateS3Stats(stats) {
        if (stats.error) {
            $('#s3Stats').html(`<span class="text-danger">Error: ${stats.error}</span>`);
            return;
        }
        
        $('#s3Stats').html(`
            <div><strong>${stats.audio_files}</strong> audio files</div>
            <div><strong>${stats.total_size_mb} MB</strong> total size</div>
            <div class="text-muted small">${stats.bucket}/${stats.prefix}</div>
        `);
    }
    
    async downloadS3Recording(s3Key, filename) {
        try {
            this.showLoading();
            
            const response = await $.ajax({
                url: `/api/s3/download/${encodeURIComponent(s3Key)}`,
                type: 'POST'
            });
            
            this.showSuccess(response.message);
            
            // Refresh main data
            setTimeout(() => this.refreshData(), 2000);
            
        } catch (error) {
            console.error('Error downloading S3 recording:', error);
            this.showError('Download failed: ' + (error.responseJSON?.error || 'Unknown error'));
        } finally {
            this.hideLoading();
        }
    }
    
    async downloadAllNewRecordings() {
        try {
            this.showLoading();
            
            const response = await $.ajax({
                url: '/api/s3/sync',
                type: 'POST'
            });
            
            this.showSuccess(response.message);
            
            // Close modal and refresh data
            $('#s3Modal').modal('hide');
            
            if (response.downloaded_count > 0) {
                setTimeout(() => this.refreshData(), 2000);
            }
            
        } catch (error) {
            console.error('Error downloading all recordings:', error);
            this.showError('Bulk download failed: ' + (error.responseJSON?.error || 'Unknown error'));
        } finally {
            this.hideLoading();
        }
    }
    
    // Analytics Functions
    async loadAnalytics() {
        try {
            // Load all analytics components in parallel
            await Promise.all([
                this.loadIntentDistribution(),
                this.loadSubIntentDistribution(),
                this.loadIntentSubIntentBreakdown(),
                this.loadDurationDistribution(),
                this.loadSpeakerDistribution(),
                this.loadDropOffAnalysis(),
                this.loadDailyTrends(),
                this.loadDispositionDistribution()
            ]);
        } catch (error) {
            console.error('Error loading analytics:', error);
        }
    }
    
    async loadIntentDistribution() {
        try {
            const response = await $.ajax({
                url: '/api/analytics/intents',
                type: 'GET'
            });
            
            this.renderIntentChart(response);
            $('#intentChartLoading').hide();
            
        } catch (error) {
            console.error('Error loading intent distribution:', error);
            $('#intentChartLoading').html('<p class="text-danger">Failed to load intent distribution</p>');
        }
    }
    
    async loadDailyTrends() {
        try {
            const response = await $.ajax({
                url: '/api/analytics/trends?days=7',
                type: 'GET'
            });
            
            this.renderTrendsChart(response);
            $('#trendsChartLoading').hide();
            
        } catch (error) {
            console.error('Error loading daily trends:', error);
            $('#trendsChartLoading').html('<p class="text-danger">Failed to load daily trends</p>');
        }
    }
    
    async loadHourlyDistribution() {
        try {
            const response = await $.ajax({
                url: '/api/analytics/hourly',
                type: 'GET'
            });
            
            this.renderHourlyChart(response);
            $('#hourlyChartLoading').hide();
            
        } catch (error) {
            console.error('Error loading hourly distribution:', error);
            $('#hourlyChartLoading').html('<p class="text-danger">Failed to load hourly distribution</p>');
        }
    }
    
    async loadSubIntentDistribution() {
        try {
            const response = await $.ajax({
                url: '/api/analytics/sub-intents',
                type: 'GET'
            });
            
            this.renderSubIntentChart(response);
            $('#subIntentChartLoading').hide();
            
        } catch (error) {
            console.error('Error loading sub-intent distribution:', error);
            $('#subIntentChartLoading').html('<p class="text-danger">Failed to load sub-intent distribution</p>');
        }
    }
    
    async loadDurationDistribution() {
        try {
            const response = await $.ajax({
                url: '/api/analytics/duration-distribution',
                type: 'GET'
            });
            
            this.renderDurationChart(response);
            $('#durationDistributionChartLoading').hide();
            
        } catch (error) {
            console.error('Error loading duration distribution:', error);
            $('#durationDistributionChartLoading').html('<p class="text-danger">Failed to load duration distribution</p>');
        }
    }
    
    async loadSpeakerDistribution() {
        try {
            const response = await $.ajax({
                url: '/api/analytics/speaker-distribution',
                type: 'GET'
            });
            
            this.renderSpeakerChart(response);
            $('#speakerCountChartLoading').hide();
            
        } catch (error) {
            console.error('Error loading speaker distribution:', error);
            $('#speakerCountChartLoading').html('<p class="text-danger">Failed to load speaker distribution</p>');
        }
    }
    
    async loadDropOffAnalysis() {
        try {
            const response = await $.ajax({
                url: '/api/analytics/drop-off-analysis',
                type: 'GET'
            });
            
            this.renderDropOffAnalysis(response);
            $('#dropoffAnalysisLoading').hide();
            
        } catch (error) {
            console.error('Error loading drop-off analysis:', error);
            $('#dropoffAnalysisLoading').html('<p class="text-danger">Failed to load drop-off analysis</p>');
        }
    }
    
    async loadIntentSubIntentBreakdown() {
        try {
            const response = await $.ajax({
                url: '/api/analytics/intent-sub-intent-breakdown',
                type: 'GET'
            });
            
            this.renderIntentSubIntentBreakdown(response);
            $('#intentSubIntentBreakdownLoading').hide();
            
        } catch (error) {
            console.error('Error loading intent sub-intent breakdown:', error);
            $('#intentSubIntentBreakdownLoading').html('<p class="text-danger">Failed to load intent sub-intent breakdown</p>');
        }
    }
    
    async loadDispositionDistribution() {
        try {
            const response = await $.ajax({
                url: '/api/analytics/disposition-distribution',
                type: 'GET'
            });
            
            this.renderDispositionCharts(response);
            $('#primaryDispositionChartLoading').hide();
            $('#secondaryDispositionChartLoading').hide();
            
            // Update classification rate
            $('#classificationRate').text(`${response.classification_rate}% classified`);
            
        } catch (error) {
            console.error('Error loading disposition distribution:', error);
            $('#primaryDispositionChartLoading').html('<p class="text-danger">Failed to load disposition distribution</p>');
            $('#secondaryDispositionChartLoading').html('<p class="text-danger">Failed to load disposition distribution</p>');
        }
    }
    
    async classifyDispositions() {
        try {
            this.showLoading();
            $('#classifyDispositionsBtn').prop('disabled', true).html('<i class="bi bi-hourglass-split me-1"></i>Classifying...');
            
            const response = await $.ajax({
                url: '/api/classify-dispositions',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({})
            });
            
            this.showSuccess(response.message);
            
            // Reload disposition charts and table data
            await this.loadDispositionDistribution();
            await this.loadData();
            
        } catch (error) {
            console.error('Error classifying dispositions:', error);
            this.showError('Failed to classify dispositions: ' + (error.responseJSON?.error || 'Unknown error'));
        } finally {
            $('#classifyDispositionsBtn').prop('disabled', false).html('<i class="bi bi-robot me-1"></i>Classify');
            this.hideLoading();
        }
    }
    
    async loadKeyInsights() {
        console.log('Loading key insights...');
        try {
            const response = await $.ajax({
                url: '/api/analytics/insights',
                type: 'GET'
            });
            
            console.log('Key insights response:', response);
            this.renderInsights(response.insights || []);
            $('.insight-loading').hide();
            console.log('Key insights loaded successfully');
            
        } catch (error) {
            console.error('Error loading key insights:', error);
            $('.insight-loading').html('<p class="text-danger">Failed to load insights</p>');
        }
    }
    
    renderIntentChart(data) {
        const ctx = document.getElementById('intentChart');
        if (!ctx) return;
        
        const counts = data.intents.map(intent => intent.count);
        const totalCount = counts.reduce((sum, count) => sum + count, 0);
        
        // Create labels with percentages
        const labelsWithPercentages = data.intents.map(intent => {
            const percentage = totalCount > 0 ? ((intent.count / totalCount) * 100).toFixed(1) : 0;
            return `${intent.label} (${percentage}%)`;
        });
        
        const colors = [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', 
            '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
        ];
        
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labelsWithPercentages,
                datasets: [{
                    data: counts,
                    backgroundColor: colors,
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = data.intents[context.dataIndex].label;
                                const count = context.raw;
                                const percentage = totalCount > 0 ? ((count / totalCount) * 100).toFixed(1) : 0;
                                return `${label}: ${count} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    renderTrendsChart(data) {
        const ctx = document.getElementById('trendsChart');
        if (!ctx) return;
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.dates,
                datasets: [{
                    label: 'Total Calls',
                    data: data.total_calls,
                    borderColor: '#36A2EB',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: 'Completed Calls',
                    data: data.completed_calls,
                    borderColor: '#4BC0C0',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        position: 'top',
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    renderHourlyChart(data) {
        const ctx = document.getElementById('hourlyChart');
        if (!ctx) return;
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.hours,
                datasets: [{
                    label: 'Calls per Hour',
                    data: data.calls,
                    backgroundColor: 'rgba(54, 162, 235, 0.8)',
                    borderColor: '#36A2EB',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    renderSubIntentChart(data) {
        const ctx = document.getElementById('subIntentChart');
        if (!ctx) return;
        
        if (!data.sub_intents || data.sub_intents.length === 0) {
            $('#subIntentChartLoading').html('<p class="text-muted">No sub-intent data available</p>');
            return;
        }
        
        const counts = data.sub_intents.map(subIntent => subIntent.count);
        const totalCount = counts.reduce((sum, count) => sum + count, 0);
        
        // Create labels with percentages
        const labelsWithPercentages = data.sub_intents.map(subIntent => {
            const percentage = totalCount > 0 ? ((subIntent.count / totalCount) * 100).toFixed(1) : 0;
            return `${subIntent.label} (${percentage}%)`;
        });
        
        const colors = [
            '#17A2B8', '#28A745', '#FFC107', '#DC3545', 
            '#6F42C1', '#FD7E14', '#20C997', '#E83E8C'
        ];
        
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labelsWithPercentages,
                datasets: [{
                    data: counts,
                    backgroundColor: colors,
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: {
                                size: 11
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = data.sub_intents[context.dataIndex].label;
                                const count = context.raw;
                                const percentage = totalCount > 0 ? ((count / totalCount) * 100).toFixed(1) : 0;
                                return `${label}: ${count} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    renderDurationChart(data) {
        const ctx = document.getElementById('durationDistributionChart');
        if (!ctx) return;
        
        if (!data.duration_ranges || data.duration_ranges.length === 0) {
            $('#durationDistributionChartLoading').html('<p class="text-muted">No duration data available</p>');
            return;
        }
        
        const labels = data.duration_ranges.map(range => range.range);
        const counts = data.duration_ranges.map(range => range.count);
        const percentages = data.duration_ranges.map(range => range.percentage);
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Number of Calls',
                    data: counts,
                    backgroundColor: [
                        '#DC3545', // Red for very short (drop-offs)
                        '#FFC107', // Yellow for short
                        '#28A745', // Green for normal
                        '#17A2B8', // Blue for longer
                        '#6F42C1', // Purple for long
                        '#FD7E14'  // Orange for very long
                    ],
                    borderColor: '#fff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const index = context.dataIndex;
                                const count = context.raw;
                                const percentage = percentages[index];
                                return `${count} calls (${percentage}%)`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Calls'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Call Duration'
                        }
                    }
                }
            }
        });
    }
    
    renderSpeakerChart(data) {
        const ctx = document.getElementById('speakerCountChart');
        if (!ctx) return;
        
        if (!data.speaker_counts || data.speaker_counts.length === 0) {
            $('#speakerCountChartLoading').html('<p class="text-muted">No speaker data available</p>');
            return;
        }
        
        const labels = data.speaker_counts.map(item => item.label);
        const counts = data.speaker_counts.map(item => item.calls);
        const colors = ['#DC3545', '#28A745', '#17A2B8']; // Red for single speaker (drop-offs), green for normal, blue for multi
        
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: counts,
                    backgroundColor: colors,
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const index = context.dataIndex;
                                const count = context.raw;
                                const percentage = data.speaker_counts[index].percentage;
                                const description = data.speaker_counts[index].description;
                                return [`${count} calls (${percentage}%)`, description];
                            }
                        }
                    }
                }
            }
        });
    }
    
    renderDropOffAnalysis(data) {
        const container = $('#dropoffAnalysisContainer');
        if (!container.length) return;
        
        container.find('#dropoffAnalysisLoading').hide();
        
        if (!data.analysis || data.analysis.length === 0) {
            container.html('<p class="text-muted text-center">No drop-off analysis data available</p>');
            return;
        }
        
        let analysisHtml = '<div class="drop-off-analysis">';
        
        // Overall drop-off rate
        analysisHtml += `
            <div class="alert alert-info mb-3">
                <h6 class="mb-2"><i class="bi bi-info-circle me-2"></i>Overall Drop-off Rate</h6>
                <div class="d-flex justify-content-between align-items-center">
                    <span><strong>${data.drop_off_rate}%</strong> of calls show drop-off indicators</span>
                    <span class="text-muted">${data.drop_offs} / ${data.total_calls} calls</span>
                </div>
            </div>
        `;
        
        // Analysis breakdown
        analysisHtml += '<div class="row">';
        
        data.analysis.forEach((item, index) => {
            const colorClass = item.percentage > 30 ? 'danger' : item.percentage > 15 ? 'warning' : 'success';
            
            analysisHtml += `
                <div class="col-md-6 mb-3">
                    <div class="card border-${colorClass}">
                        <div class="card-body p-3">
                            <h6 class="card-title text-${colorClass}">${item.type}</h6>
                            <div class="d-flex justify-content-between mb-2">
                                <span class="fw-bold">${item.count} calls</span>
                                <span class="badge bg-${colorClass}">${item.percentage}%</span>
                            </div>
                            <p class="card-text small text-muted mb-0">${item.description}</p>
                        </div>
                    </div>
                </div>
            `;
        });
        
        analysisHtml += '</div></div>';
        
        container.html(analysisHtml);
    }
    
    renderIntentSubIntentBreakdown(data) {
        const container = $('#intentSubIntentBreakdownContainer');
        if (!container.length) return;
        
        if (!data.breakdown || Object.keys(data.breakdown).length === 0) {
            container.html('<div class="col-12"><p class="text-muted text-center">No intent breakdown data available</p></div>');
            return;
        }
        
        // Clear existing content
        container.empty();
        
        // Create charts for each intent with 3 per row
        Object.entries(data.breakdown).forEach(([intent, intentData], index) => {
            if (intentData.sub_intents && intentData.sub_intents.length > 0) {
                const chartId = `subIntentChart_${intent.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_]/g, '')}`;
                
                const chartHtml = `
                    <div class="col-lg-4 col-md-6 col-sm-12 mb-4">
                        <div class="card h-100 shadow-sm">
                            <div class="card-header bg-primary text-white">
                                <h6 class="mb-0">
                                    <i class="bi bi-pie-chart-fill me-2"></i>
                                    ${intentData.label}
                                    <small class="opacity-75 ms-2">(${intentData.total_count} calls)</small>
                                </h6>
                            </div>
                            <div class="card-body p-3">
                                <div style="position: relative; height: 250px;">
                                    <canvas id="${chartId}"></canvas>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                
                container.append(chartHtml);
                
                // Create the chart after DOM is updated
                setTimeout(() => {
                    const canvas = document.getElementById(chartId);
                    if (canvas) {
                        const colors = [
                            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', 
                            '#9966FF', '#FF9F40', '#28A745', '#DC3545'
                        ];
                        
                        new Chart(canvas, {
                            type: 'doughnut',
                            data: {
                                labels: intentData.sub_intents.map(sub => sub.label),
                                datasets: [{
                                    data: intentData.sub_intents.map(sub => sub.count),
                                    backgroundColor: colors.slice(0, intentData.sub_intents.length),
                                    borderWidth: 2,
                                    borderColor: '#fff',
                                    hoverBorderWidth: 3
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                cutout: '60%',
                                plugins: {
                                    legend: {
                                        position: 'bottom',
                                        labels: {
                                            boxWidth: 12,
                                            font: {
                                                size: 11
                                            },
                                            padding: 15,
                                            generateLabels: function(chart) {
                                                const data = chart.data;
                                                if (data.labels.length && data.datasets.length) {
                                                    return data.labels.map((label, index) => {
                                                        const count = data.datasets[0].data[index];
                                                        const percentage = ((count / intentData.total_count) * 100).toFixed(1);
                                                        return {
                                                            text: `${label} (${percentage}%)`,
                                                            fillStyle: data.datasets[0].backgroundColor[index],
                                                            strokeStyle: data.datasets[0].borderColor,
                                                            lineWidth: data.datasets[0].borderWidth,
                                                            index: index
                                                        };
                                                    });
                                                }
                                                return [];
                                            }
                                        }
                                    },
                                    tooltip: {
                                        callbacks: {
                                            label: function(context) {
                                                const percentage = ((context.parsed / intentData.total_count) * 100).toFixed(1);
                                                return `${context.label}: ${context.parsed} calls (${percentage}%)`;
                                            }
                                        }
                                    }
                                },
                                interaction: {
                                    intersect: false
                                }
                            }
                        });
                    }
                }, 100);
            }
        });
    }
    
    renderDispositionCharts(data) {
        // Primary Disposition Chart
        const primaryCtx = document.getElementById('primaryDispositionChart');
        if (primaryCtx && data.primary_dispositions && data.primary_dispositions.length > 0) {
            const colors = [
                '#28a745', '#007bff', '#ffc107', '#dc3545', '#17a2b8',
                '#6c757d', '#f8f9fa', '#343a40', '#17a2b8', '#ffc107'
            ];
            
            // Filter out any invalid data
            const validPrimaryData = data.primary_dispositions.filter(d => 
                d && d.label && d.count && !isNaN(d.count) && d.count > 0
            );
            
            if (validPrimaryData.length === 0) {
                $('#primaryDispositionChart').parent().html('<p class="text-muted text-center">No primary disposition data available</p>');
                return;
            }
            
            new Chart(primaryCtx, {
                type: 'doughnut',
                data: {
                    labels: validPrimaryData.map(d => d.label.replace(/_/g, ' ')),
                    datasets: [{
                        data: validPrimaryData.map(d => d.count),
                        backgroundColor: colors.slice(0, validPrimaryData.length),
                        borderWidth: 2,
                        borderColor: '#fff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                generateLabels: function(chart) {
                                    const data = chart.data;
                                    if (data.labels.length && data.datasets.length) {
                                        const totalPrimary = data.datasets[0].data.reduce((sum, val) => sum + val, 0);
                                        return data.labels.map((label, index) => {
                                            const count = data.datasets[0].data[index];
                                            const percentage = ((count / totalPrimary) * 100).toFixed(1);
                                            return {
                                                text: `${label} (${percentage}%)`,
                                                fillStyle: data.datasets[0].backgroundColor[index],
                                                strokeStyle: data.datasets[0].borderColor,
                                                lineWidth: data.datasets[0].borderWidth,
                                                index: index
                                            };
                                        });
                                    }
                                    return [];
                                }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const totalPrimary = context.dataset.data.reduce((sum, val) => sum + val, 0);
                                    const percentage = ((context.parsed / totalPrimary) * 100).toFixed(1);
                                    return `${context.label}: ${context.parsed} calls (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });
        }
        
        // Secondary Disposition Chart
        const secondaryCtx = document.getElementById('secondaryDispositionChart');
        if (secondaryCtx && data.secondary_dispositions && data.secondary_dispositions.length > 0) {
            const colors = [
                '#28a745', '#007bff', '#ffc107', '#dc3545', '#17a2b8',
                '#6c757d', '#28a745', '#17a2b8', '#ffc107', '#6c757d',
                '#007bff', '#17a2b8', '#f8f9fa'
            ];
            
            // Filter out any invalid data
            const validSecondaryData = data.secondary_dispositions.filter(d => 
                d && d.label && d.count && !isNaN(d.count) && d.count > 0
            );
            
            if (validSecondaryData.length === 0) {
                $('#secondaryDispositionChart').parent().html('<p class="text-muted text-center">No secondary disposition data available</p>');
                return;
            }
            
            new Chart(secondaryCtx, {
                type: 'doughnut',
                data: {
                    labels: validSecondaryData.map(d => d.label.replace(/_/g, ' ')),
                    datasets: [{
                        data: validSecondaryData.map(d => d.count),
                        backgroundColor: colors.slice(0, validSecondaryData.length),
                        borderWidth: 2,
                        borderColor: '#fff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                generateLabels: function(chart) {
                                    const data = chart.data;
                                    if (data.labels.length && data.datasets.length) {
                                        const totalSecondary = data.datasets[0].data.reduce((sum, val) => sum + val, 0);
                                        return data.labels.map((label, index) => {
                                            const count = data.datasets[0].data[index];
                                            const percentage = ((count / totalSecondary) * 100).toFixed(1);
                                            return {
                                                text: `${label} (${percentage}%)`,
                                                fillStyle: data.datasets[0].backgroundColor[index],
                                                strokeStyle: data.datasets[0].borderColor,
                                                lineWidth: data.datasets[0].borderWidth,
                                                index: index
                                            };
                                        });
                                    }
                                    return [];
                                }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const totalSecondary = context.dataset.data.reduce((sum, val) => sum + val, 0);
                                    const percentage = ((context.parsed / totalSecondary) * 100).toFixed(1);
                                    return `${context.label}: ${context.parsed} calls (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });
        }
    }
    
    renderInsights(insights) {
        console.log('Rendering insights:', insights);
        const container = $('#insightsList');
        console.log('Insights container found:', container.length > 0);
        
        if (container.length === 0) {
            console.error('Insights container #insightsList not found!');
            return;
        }
        
        container.empty();
        
        if (!insights || insights.length === 0) {
            console.log('No insights to render');
            container.append('<p class="text-muted">No insights available</p>');
            return;
        }
        
        console.log('Rendering', insights.length, 'insights');
        insights.forEach((insight, index) => {
            console.log(`Rendering insight ${index + 1}:`, insight);
            const iconClass = this.getInsightIcon(insight.icon);
            const insightHtml = `
                <div class="insight-item">
                    <div class="insight-icon">
                        <i class="bi ${iconClass}"></i>
                    </div>
                    <div class="insight-content">
                        <h6 class="insight-title">${insight.title}</h6>
                        <p class="insight-description">${insight.description}</p>
                        <span class="insight-value">${insight.value}</span>
                    </div>
                </div>
            `;
            container.append(insightHtml);
        });
        console.log('Insights rendering completed');
    }
    
    getInsightIcon(iconName) {
        const iconMap = {
            'clock': 'bi-clock-fill',
            'bullseye': 'bi-bullseye',
            'lightning': 'bi-lightning-fill',
            'check-circle': 'bi-check-circle-fill',
            'trend-up': 'bi-trending-up',
            'trend-down': 'bi-trending-down'
        };
        return iconMap[iconName] || 'bi-info-circle-fill';
    }
    
    
    showSummaryModal(filename, summary) {
        $('#summaryModalTitle').text(`Summary - ${filename}`);
        $('#summaryModalContent').text(summary);
        $('#summaryModal').modal('show');
    }
    
    async showTranscriptModal(filename) {
        console.log('showTranscriptModal called with filename:', filename);
        try {
            console.log('Showing loading...');
            this.showLoading();
            
            console.log('Fetching file details for:', filename);
            // Fetch the full file details which includes the transcription
            const response = await fetch(`/api/file/${encodeURIComponent(filename)}`);
            console.log('API response status:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('File data received:', data);
            console.log('Transcription:', data.transcription);
            console.log('Diarized Transcription:', data.diarized_transcription);
            
            // Check if modal elements exist
            const modalTitle = $('#transcriptModalTitle');
            const modalContent = $('#transcriptModalContent');
            const modal = $('#transcriptModal');
            
            console.log('Modal title element found:', modalTitle.length > 0);
            console.log('Modal content element found:', modalContent.length > 0);
            console.log('Modal element found:', modal.length > 0);
            
            // Set the modal title and subtitle
            modalTitle.html(`<i class="bi bi-chat-dots me-2"></i>Call Transcript`);
            $('#transcriptModalSubtitle').text(`${filename}`);
            
            // Render chat-style transcription
            this.renderChatStyleTranscription(modalContent, data.diarized_transcription, data.transcription);
            
            console.log('Showing modal...');
            // Show the modal
            modal.modal('show');
            
        } catch (error) {
            console.error('Error loading transcript:', error);
            this.showError('Failed to load transcript: ' + error.message);
        } finally {
            console.log('Hiding loading...');
            this.hideLoading();
        }
    }
    
    renderChatStyleTranscription(container, diarizedTranscription, fallbackTranscription) {
        /**Render transcription as chat-style alternating speaker bubbles.**/
        
        if (!diarizedTranscription && !fallbackTranscription) {
            container.html('<p class="text-muted">No transcription available</p>');
            return;
        }
        
        // If we have diarized transcription, use it for chat bubbles
        if (diarizedTranscription) {
            const lines = diarizedTranscription.split('\n').filter(line => line.trim());
            let renderedHtml = '';
            
            lines.forEach((line, index) => {
                const speakerMatch = line.match(/^Speaker (\d+):\s*(.*)$/);
                if (speakerMatch) {
                    const speakerNum = speakerMatch[1];
                    const text = speakerMatch[2];
                    
                    // Assign clean messaging styles based on speaker
                    const speakerStyles = {
                        '1': { type: 'agent', avatar: 'A', bubbleClass: 'bubble-agent', avatarClass: 'avatar-agent' },
                        '2': { type: 'customer', avatar: 'C', bubbleClass: 'bubble-customer', avatarClass: 'avatar-customer' },
                        '3': { type: 'agent', avatar: '3', bubbleClass: 'bubble-agent', avatarClass: 'avatar-agent' },
                        '4': { type: 'customer', avatar: '4', bubbleClass: 'bubble-customer', avatarClass: 'avatar-customer' },
                        '5': { type: 'agent', avatar: '5', bubbleClass: 'bubble-agent', avatarClass: 'avatar-agent' }
                    };
                    
                    const style = speakerStyles[speakerNum] || { type: 'agent', avatar: speakerNum, bubbleClass: 'bubble-agent', avatarClass: 'avatar-agent' };
                    
                    renderedHtml += `
                        <div class="chat-message ${style.type}">
                            ${style.type === 'agent' ? `<div class="message-avatar ${style.avatarClass}">${style.avatar}</div>` : ''}
                            <div class="message-bubble ${style.bubbleClass}">
                                ${text}
                            </div>
                            ${style.type === 'customer' ? `<div class="message-avatar ${style.avatarClass}">${style.avatar}</div>` : ''}
                        </div>
                    `;
                } else if (line.trim()) {
                    // Fallback for non-speaker lines
                    renderedHtml += `
                        <div class="system-message">
                            ${line}
                        </div>
                    `;
                }
            });
            
            // Create clean messaging interface like the reference image
            container.html(`
                <style>
                    .chat-interface {
                        height: 100%;
                        background: #f5f7fa;
                        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        display: flex;
                        flex-direction: column;
                    }
                    
                    .chat-messages-area {
                        flex: 1;
                        padding: 20px;
                        overflow-y: auto;
                        background: #f5f7fa;
                    }
                    
                    .chat-messages-area::-webkit-scrollbar {
                        width: 6px;
                    }
                    
                    .chat-messages-area::-webkit-scrollbar-track {
                        background: transparent;
                    }
                    
                    .chat-messages-area::-webkit-scrollbar-thumb {
                        background: rgba(0,0,0,0.1);
                        border-radius: 3px;
                    }
                    
                    .chat-message {
                        margin-bottom: 16px;
                        display: flex;
                        align-items: flex-end;
                    }
                    
                    .chat-message.agent {
                        justify-content: flex-start;
                    }
                    
                    .chat-message.customer {
                        justify-content: flex-end;
                    }
                    
                    .message-avatar {
                        width: 32px;
                        height: 32px;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 12px;
                        font-weight: 600;
                        color: white;
                        margin: 0 8px;
                        flex-shrink: 0;
                    }
                    
                    .avatar-agent {
                        background: #6b7280;
                    }
                    
                    .avatar-customer {
                        background: #3b82f6;
                    }
                    
                    .message-bubble {
                        max-width: 60%;
                        padding: 12px 16px;
                        border-radius: 20px;
                        font-size: 14px;
                        line-height: 1.4;
                        word-wrap: break-word;
                        position: relative;
                    }
                    
                    .bubble-agent {
                        background: #ffffff;
                        color: #374151;
                        border: 1px solid #e5e7eb;
                        border-bottom-left-radius: 8px;
                        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                    }
                    
                    .bubble-customer {
                        background: #3b82f6;
                        color: white;
                        border-bottom-right-radius: 8px;
                    }
                    
                    .message-time {
                        font-size: 11px;
                        color: #9ca3af;
                        margin-top: 4px;
                        text-align: center;
                    }
                    
                    .system-message {
                        text-align: center;
                        margin: 16px 0;
                        font-size: 12px;
                        color: #6b7280;
                        font-style: italic;
                    }
                </style>
                
                <div class="chat-interface">
                    <div class="chat-messages-area">
                        ${renderedHtml}
                    </div>
                </div>
            `);
        } else {
            // Fallback to regular transcription if no diarized version
            container.html(`
                <div class="regular-transcript bg-light p-3 rounded">
                    <div class="text-muted small mb-2">Regular Transcription:</div>
                    <pre style="white-space: pre-wrap; font-family: inherit;">${fallbackTranscription}</pre>
                </div>
            `);
        }
    }
    
    // Utility functions for loading states and error handling
    showLoading() {
        console.log('Showing loading state');
        $('#loadingSpinner').removeClass('d-none').show();
    }
    
    hideLoading() {
        console.log('Hiding loading state');
        $('#loadingSpinner').addClass('d-none').hide();
    }
    
    showError(message) {
        console.error('Showing error:', message);
        // Create a toast or alert for the error
        const alertHtml = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                <i class="bi bi-exclamation-triangle-fill me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // Add the alert to the top of the main content area
        $('.container-fluid').first().prepend(alertHtml);
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            $('.alert-danger').fadeOut();
        }, 5000);
    }
    
    renderDiarizedTranscription(diarizedTranscription) {
        /**Render diarized transcription with speaker styling.**/
        const container = $('#detailDiarizedTranscription');
        
        if (!diarizedTranscription) {
            container.html('<p class="text-muted">No speaker-separated transcription available</p>');
            return;
        }
        
        // Split by lines and render each speaker's part
        const lines = diarizedTranscription.split('\n').filter(line => line.trim());
        let renderedHtml = '';
        
        lines.forEach(line => {
            const speakerMatch = line.match(/^Speaker (\d+):\s*(.*)$/);
            if (speakerMatch) {
                const speakerNum = speakerMatch[1];
                const text = speakerMatch[2];
                
                // Assign colors based on speaker number
                const speakerColors = {
                    '1': 'primary',
                    '2': 'success', 
                    '3': 'warning',
                    '4': 'info',
                    '5': 'secondary'
                };
                
                const colorClass = speakerColors[speakerNum] || 'secondary';
                
                renderedHtml += `
                    <div class="speaker-line mb-2 p-2 border-start border-3 border-${colorClass}">
                        <div class="d-flex align-items-start">
                            <span class="badge bg-${colorClass} me-2 flex-shrink-0">Speaker ${speakerNum}</span>
                            <span class="text-dark">${text}</span>
                        </div>
                    </div>
                `;
            } else {
                // Fallback for non-speaker lines
                renderedHtml += `<p class="text-muted">${line}</p>`;
            }
        });
        
        container.html(renderedHtml);
    }
}

// Initialize dashboard when script loads
const dashboard = new AudioTranscriptionDashboard();