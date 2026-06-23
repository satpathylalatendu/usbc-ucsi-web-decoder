// UCSI Decoder Web Application - JavaScript

// Global state
let selectedCommand = null;
let selectedPort = 1;
let decodeHistory = [];
let detectedVersion = '3.0';
let currentDecodedResult = null;
let allDecodedResults = []; // Accumulate all command results for batch saving
let aardvarkMode = false;
let numDetectedPorts = 0; // Number of ports detected from GET_CAPABILITY
let detectedAlternateModes = []; // Alternate modes detected from GET_ALTERNATE_MODES
let platformInfo = { platform: 'Windows', ucsi_path: '', is_linux: false, is_windows: true }; // Platform detection

// Sample data for testing
const SAMPLE_DATA = {
    capability: {
        command: '0x06 - GET_CAPABILITY',
        hex: '0704000002800000010010032003000200'
    },
    connector_status: {
        command: '0x12 - GET_CONNECTOR_STATUS',
        hex: '0000190B010000002C01000000000000000000'
    },
    pdos: {
        command: '0x10 - GET_PDOS (Local Source)',
        hex: '2D019096B4019096F801909664029096'
    }
};

// Command Applicability Information (UCSI Spec Table 6-87)
// N = Normative (Shall be supported), CN = Conditional Normative, O = Optional, NA = Not Applicable, NS = Not Supported, R = Reserved
const COMMAND_APPLICABILITY = {
    'PPM_RESET': { OPM: 'CN', PPM: 'N', LPM: 'NS', note: 'CN1: Not applicable if system does not have PPM or PPM works in pass-through mode. NS2: If LPM controls two connectors and performs PPM role.' },
    'CANCEL': { OPM: 'N', PPM: 'N', LPM: 'N', note: 'Shall be supported by all.' },
    'CONNECTOR_RESET': { OPM: 'N', PPM: 'NA', LPM: 'N', note: 'Shall be supported by OPM and LPM.' },
    'ACK_CC_CI': { OPM: 'N', PPM: 'N', LPM: 'CN', note: 'CN3: Applicable if PPM is in pass-through mode or in OPM-LPM configuration.' },
    'SET_NOTIFICATION_ENABLE': { OPM: 'O', PPM: 'N', LPM: 'N', note: 'Optional for OPM, required for PPM and LPM.' },
    'GET_CAPABILITY': { OPM: 'O', PPM: 'N', LPM: 'CN', note: 'CN3: Applicable if PPM is in pass-through mode or in OPM-LPM configuration.' },
    'GET_CONNECTOR_CAPABILITY': { OPM: 'N', PPM: 'NA', LPM: 'N', note: 'Shall be supported by OPM and LPM.' },
    'SET_CCOM': { OPM: 'O', PPM: 'O', LPM: 'CN', note: 'CN5: Supports only if the connector is DRP.' },
    'SET_UOM': { OPM: 'N', PPM: 'NA', LPM: 'N', note: 'Shall be supported by OPM and LPM.' },
    'SET_PDM': { OPM: 'N', PPM: 'NA', LPM: 'N', note: 'Shall be supported by OPM and LPM.' },
    'GET_ALTERNATE_MODES': { OPM: 'O', PPM: 'O', LPM: 'CN', note: 'CN6: Shall support if connector supports any Alternate modes.' },
    'GET_CAM_SUPPORTED': { OPM: 'O', PPM: 'O', LPM: 'CN', note: 'CN6: Shall support if connector supports any Alternate modes.' },
    'GET_CURRENT_CAM': { OPM: 'O', PPM: 'O', LPM: 'CN', note: 'CN6: Shall support if connector supports any Alternate modes.' },
    'SET_NEW_CAM': { OPM: 'O', PPM: 'NA', LPM: 'CN', note: 'CN6: Shall support if connector supports any Alternate modes.' },
    'SET_USB': { OPM: 'O', PPM: 'CN', LPM: 'CN', note: 'CN4: PPM conditional. CN10: LPM if OPM supports this command and it supports USB3/USB4 modes.' },
    'GET_PDOS': { OPM: 'N', PPM: 'NA', LPM: 'N', note: 'Shall be supported by OPM and LPM.' },
    'GET_CABLE_PROPERTY': { OPM: 'O', PPM: 'O', LPM: 'N', note: 'Optional for OPM and PPM, required for LPM.' },
    'GET_CONNECTOR_STATUS': { OPM: 'N', PPM: 'N', LPM: 'N', note: 'Shall be supported by all.' },
    'GET_ERROR_STATUS': { OPM: 'N', PPM: 'N', LPM: 'N', note: 'Shall be supported by all.' },
    'SET_POWER_LEVEL': { OPM: 'N', PPM: 'N', LPM: 'N', note: 'Shall be supported by all. Always supported for backward compatibility.' },
    'GET_PD_MESSAGE': { OPM: 'O', PPM: 'NA', LPM: 'CN', note: 'CN9: If port partner device is PD capable and command is supported.' },
    'GET_ATTENTION_VDO': { OPM: 'O', PPM: 'NA', LPM: 'CN', note: 'CN9: If port partner device is PD capable and command is supported.' },
    'GET_CAM_CS': { OPM: 'O', PPM: 'NA', LPM: 'CN', note: 'CN6: Shall support if connector supports any Alternate modes.' },
    'LPM_FW_UPDATE_REQUEST': { OPM: 'O', PPM: 'NA', LPM: 'O', note: 'Optional for OPM and LPM.' },
    'SECURITY_REQUEST': { OPM: 'O', PPM: 'NA', LPM: 'O', note: 'Optional for OPM and LPM.' },
    'SET_RETIMER_MODE': { OPM: 'O', PPM: 'NA', LPM: 'O', note: 'Optional for OPM and LPM.' },
    'SET_SINK_PATH': { OPM: 'N', PPM: 'NA', LPM: 'R', note: 'Reserved for LPM.' },
    'CHUNKING_SUPPORT': { OPM: 'N', PPM: 'NA', LPM: 'CN', note: 'CN8: Applicable if Message In/Out data structures supported by PPM/LPM are less than prescribed.' },
    'SET_PDOS': { OPM: 'N', PPM: 'NA', LPM: 'N', note: 'Shall be supported by OPM and LPM.' },
    'VENDOR_DEFINED_COMMAND': { OPM: 'O', PPM: 'NA', LPM: 'O', note: 'Optional for OPM and LPM.' },
    'GET_LPM_PPM_INFO': { OPM: 'N', PPM: 'N', LPM: 'N', note: 'Shall be supported by all.' },
    'READ_POWER_LEVEL': { OPM: 'N', PPM: 'NA', LPM: 'N', note: 'Shall be supported by OPM and LPM.' }
};

// Applicability legend
const APPLICABILITY_LEGEND = {
    'N': 'Normative - Shall be supported',
    'CN': 'Conditional Normative - Shall be supported based on feature',
    'O': 'Optional - May be implemented',
    'NA': 'Not Applicable',
    'NS': 'Not Supported - Shall report not supported',
    'R': 'Reserved'
};

// Helper function to check if command is optional
function isCommandOptional(cmdKey) {
    // Extract command name from key (e.g., "5 - SET_NOTIFICATION_ENABLE" -> "SET_NOTIFICATION_ENABLE")
    const commandName = getCommandKey(cmdKey);
    if (!commandName || !COMMAND_APPLICABILITY[commandName]) {
        return { isOptional: false, note: '' };
    }
    
    const applicability = COMMAND_APPLICABILITY[commandName];
    
    // Check if any entity has optional (O), not applicable (NA), or reserved (R) designation
    const isOpmOptional = applicability.OPM === 'O' || applicability.OPM === 'NA' || applicability.OPM === 'R';
    const isPpmOptional = applicability.PPM === 'O' || applicability.PPM === 'NA' || applicability.PPM === 'R';
    const isLpmOptional = applicability.LPM === 'O' || applicability.LPM === 'NA' || applicability.LPM === 'R';
    
    // If at least one entity has it as optional/NA/reserved, consider it may not be implemented
    if (isOpmOptional || isPpmOptional || isLpmOptional) {
        let details = [];
        if (applicability.OPM === 'O') details.push('Optional for OPM');
        if (applicability.PPM === 'O') details.push('Optional for PPM');
        if (applicability.LPM === 'O') details.push('Optional for LPM');
        if (applicability.OPM === 'NA') details.push('Not Applicable for OPM');
        if (applicability.PPM === 'NA') details.push('Not Applicable for PPM');
        if (applicability.LPM === 'NA') details.push('Not Applicable for LPM');
        if (applicability.OPM === 'R') details.push('Reserved for OPM');
        if (applicability.PPM === 'R') details.push('Reserved for PPM');
        if (applicability.LPM === 'R') details.push('Reserved for LPM');
        
        return {
            isOptional: true,
            note: `${details.join(', ')} - May not be implemented. ${applicability.note || ''}`,
            applicability: applicability
        };
    }
    
    return { isOptional: false, note: '', applicability: applicability };
}

// DOM Elements
const commandList = document.getElementById('commandList');
const commandSearch = document.getElementById('commandSearch');
const selectedCommandInput = document.getElementById('selectedCommand');
const commandHexInput = document.getElementById('commandHex');
const hexResponseInput = document.getElementById('hexResponse');
const ucsiVersionSelect = document.getElementById('ucsiVersion');
const decodeBtn = document.getElementById('decodeBtn');
const clearBtn = document.getElementById('clearBtn');
const runCommandBtn = document.getElementById('runCommandBtn');
const outputArea = document.getElementById('outputArea');
const historyList = document.getElementById('historyList');
const clearHistoryBtn = document.getElementById('clearHistory');
const loadingOverlay = document.getElementById('loadingOverlay');
const tabButtons = document.querySelectorAll('.tab-button');
const portButtons = document.querySelectorAll('.port-btn');
const saveResultBtn = document.getElementById('saveResultBtn');
const copyResultBtn = document.getElementById('copyResultBtn');
const exportSummaryBtn = document.getElementById('exportSummary');
const dialogOverlay = document.getElementById('dialogOverlay');
const dialogTitle = document.getElementById('dialogTitle');
const dialogContent = document.getElementById('dialogContent');
const dialogOk = document.getElementById('dialogOk');
const dialogCancel = document.getElementById('dialogCancel');
const runAllBtn = document.getElementById('runAllBtn');
const runSelectedBtn = document.getElementById('runSelectedBtn');
const saveSummaryBtn = document.getElementById('saveSummaryBtn');
const saveAllResultsPDFBtn = document.getElementById('saveAllResultsPDFBtn');
const stressTestBtn = document.getElementById('stressTestBtn');
const runConcurrentBtn = document.getElementById('runConcurrentBtn');
const resultsChart = document.getElementById('resultsChart');
const chartMessage = document.getElementById('chartMessage');
const aardvarkModeCheckbox = document.getElementById('aardvarkMode');

// Test results tracking - per port
let testResults = {
    passed: 0,
    failed: 0,
    notRun: 0,
    total: 0,
    details: []  // {command, port, status, message}
};
let portResults = {}; // Track results per port: {port1: {passed: 0, failed: 0, notRun: 0, total: 0, details: []}, port2: {...}}
let pieChart = null;
let currentViewPort = 'all'; // 'all' or specific port number
let tooltipElement = null; // Tooltip element for command applicability
let appSessionHeartbeatTimer = null;
let appSessionHeartbeatStarted = false;

function startAppSessionHeartbeat() {
    if (appSessionHeartbeatStarted) {
        return;
    }

    appSessionHeartbeatStarted = true;

    const sendHeartbeat = () => {
        fetch('/api/browser-heartbeat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ ts: Date.now() })
        }).catch(() => {
            // Ignore transient network errors; backend timeout handles shutdown.
        });
    };

    sendHeartbeat();
    appSessionHeartbeatTimer = setInterval(sendHeartbeat, 10000);

    const sendCloseSignal = () => {
        try {
            navigator.sendBeacon('/api/browser-close', 'closing');
        } catch (e) {
            fetch('/api/browser-close', {
                method: 'POST',
                keepalive: true
            }).catch(() => {});
        }
    };

    window.addEventListener('beforeunload', sendCloseSignal);
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    setupThemeToggle();
    loadHistory();
    setupEventListeners();
    renderHistory();
    fetchPlatformInfo(); // Get platform info first, will handle platform-specific checks
    initializeChart();
    updatePortButtonStates(); // Initialize port states (all disabled initially)
    updateRunCommandButton(); // Initialize Run Command button state
    createTooltip(); // Create tooltip element
    setupCommandTooltips(); // Setup hover tooltips for commands
    setupImagePopup(); // Setup logo click popup
    setupInfrastructureVisuals(); // Premium layout interactions
    startAppSessionHeartbeat(); // Let EXE auto-close after browser closes
});

function setupThemeToggle() {
    const toggleBtn = document.getElementById('themeToggleBtn');
    if (!toggleBtn) {
        return;
    }

    const storageKey = 'ucsiThemePreference';
    const storedTheme = localStorage.getItem(storageKey);
    const preferredTheme = storedTheme || 'dark';

    applyTheme(preferredTheme);

    toggleBtn.addEventListener('click', () => {
        const currentTheme = document.body.dataset.theme === 'light' ? 'light' : 'dark';
        const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
        applyTheme(nextTheme);
        localStorage.setItem(storageKey, nextTheme);
    });
}

function applyTheme(theme) {
    const toggleBtn = document.getElementById('themeToggleBtn');
    const normalizedTheme = theme === 'light' ? 'light' : 'dark';

    document.body.dataset.theme = normalizedTheme;

    if (toggleBtn) {
        toggleBtn.textContent = normalizedTheme === 'dark' ? 'Light Mode' : 'Dark Mode';
        toggleBtn.setAttribute('aria-label', normalizedTheme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
    }
}

// Event Listeners
function setupEventListeners() {
    // Command item click
    const commandItems = document.querySelectorAll('.command-item');
    commandItems.forEach(item => {
        item.addEventListener('click', function() {
            selectCommand(this);
        });
    });

    // Tab buttons
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            switchTab(this);
        });
    });
    
    // Port buttons
    portButtons.forEach(button => {
        button.addEventListener('click', function() {
            selectPort(parseInt(this.dataset.port));
        });
    });

    // Search
    commandSearch.addEventListener('input', function() {
        filterCommands(this.value);
    });

    // Auto-decode disabled - only decode when button is clicked
    // hexResponseInput.addEventListener('input', function() {
    //     const hex = this.value.trim();
    //     if (hex.length > 0 && selectedCommand) {
    //         // Debounce the decode call
    //         clearTimeout(hexResponseInput.decodeTimer);
    //         hexResponseInput.decodeTimer = setTimeout(() => {
    //             decodeResponse();
    //         }, 500);
    //     }
    // });

    // Decode button - decode manual input
    decodeBtn.addEventListener('click', decodeResponse);

    // Run Command button
    runCommandBtn.addEventListener('click', runCommand);

    // Clear button
    clearBtn.addEventListener('click', clearForm);
    
    // Dialog buttons
    dialogOk.addEventListener('click', handleDialogOk);
    dialogCancel.addEventListener('click', closeDialog);
    
    // Save result button and dropdown
    if (saveResultBtn) {
        saveResultBtn.addEventListener('click', saveCurrentResult);
    }
    
    // Save result dropdown toggle
    const saveResultDropdown = document.getElementById('saveResultDropdown');
    const saveResultMenu = document.getElementById('saveResultMenu');
    if (saveResultDropdown && saveResultMenu) {
        saveResultDropdown.addEventListener('click', (e) => {
            e.stopPropagation();
            saveResultMenu.classList.toggle('show');
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', () => {
            saveResultMenu.classList.remove('show');
        });
    }
    
    // Copy result button
    if (copyResultBtn) {
        copyResultBtn.addEventListener('click', copyCurrentResult);
    }
    
    // Export summary button
    if (exportSummaryBtn) {
        exportSummaryBtn.addEventListener('click', exportHistorySummary);
    }

    // Clear history
    clearHistoryBtn.addEventListener('click', clearHistory);
    
    // Action buttons
    if (runAllBtn) {
        runAllBtn.addEventListener('click', runAllCommands);
    }
    if (runSelectedBtn) {
        runSelectedBtn.addEventListener('click', runSelectedCategories);
    }
    if (saveSummaryBtn) {
        saveSummaryBtn.addEventListener('click', saveSummary);
    }
    if (saveAllResultsPDFBtn) {
        saveAllResultsPDFBtn.addEventListener('click', saveAllResultsDetailedPDF);
    }
    if (stressTestBtn) {
        stressTestBtn.addEventListener('click', showStressTestDialog);
    }
    if (runConcurrentBtn) {
        runConcurrentBtn.addEventListener('click', showConcurrentTestDialog);
    }
    
    // Port filter buttons
    const filterButtons = document.querySelectorAll('.filter-btn');
    filterButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            filterButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentViewPort = this.dataset.filter;
            updateResultsChart();
        });
    });
    
    // Aardvark mode toggle
    if (aardvarkModeCheckbox) {
        aardvarkModeCheckbox.addEventListener('change', async function() {
            const isChecked = this.checked;
            
            if (isChecked) {
                // Check if Aardvark is available before enabling
                try {
                    const response = await fetch('/api/check_aardvark');
                    const data = await response.json();
                    
                    if (!data.available || !data.connected) {
                        // Aardvark not available - show custom dialog with detailed status
                        showAardvarkStatusDialog(data);
                        this.checked = false;
                        return;
                    }
                    
                    // Aardvark is available - enable mode
                    aardvarkMode = true;
                    console.log('Aardvark Mode ENABLED:', data.message);
                    
                    // Show notification instead of filling output area
                    showNotification('✓ Aardvark Mode Enabled - Commands will execute via I2C interface', 'success');
                } catch (error) {
                    console.error('Error checking Aardvark:', error);
                    showAardvarkErrorDialog('Error checking Aardvark device: ' + error.message);
                    this.checked = false;
                }
            } else {
                // Disable Aardvark mode
                aardvarkMode = false;
                console.log('Aardvark Mode DISABLED');
                
                // Show notification instead of filling output area
                showNotification('ℹ️ Aardvark Mode Disabled - Using UcsiControl.exe', 'info');
            }
        });
    }

    // Enter key in hex input
    hexResponseInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && e.ctrlKey) {
            decodeResponse();
        }
    });
}

// Create tooltip element
function createTooltip() {
    tooltipElement = document.createElement('div');
    tooltipElement.className = 'command-tooltip';
    document.body.appendChild(tooltipElement);
}

// Setup hover tooltips for commands
function setupCommandTooltips() {
    const commandItems = document.querySelectorAll('.command-item');
    
    commandItems.forEach(item => {
        item.addEventListener('mouseenter', function(e) {
            showCommandTooltip(this, e);
        });
        
        item.addEventListener('mousemove', function(e) {
            positionTooltip(e);
        });
        
        item.addEventListener('mouseleave', function() {
            hideCommandTooltip();
        });
    });
}

// Get command key from command name
function getCommandKey(commandName) {
    // Extract command key from format like "6 - GET_CAPABILITY" or "GET_CAPABILITY"
    const parts = commandName.split(' - ');
    const cmdName = parts.length > 1 ? parts[1] : parts[0];
    
    // Map command names to applicability keys
    const mapping = {
        'PPM_RESET': 'PPM_RESET',
        'CANCEL': 'CANCEL',
        'CONNECTOR_RESET': 'CONNECTOR_RESET',
        'ACK_CC_CI': 'ACK_CC_CI',
        'SET_NOTIFICATION_ENABLE': 'SET_NOTIFICATION_ENABLE',
        'GET_CAPABILITY': 'GET_CAPABILITY',
        'GET_CONNECTOR_CAPABILITY': 'GET_CONNECTOR_CAPABILITY',
        'SET_CCOM': 'SET_CCOM',
        'SET_UOM': 'SET_UOM',
        'SET_PDM': 'SET_PDM',
        'SET_PDR': 'SET_PDM',
        'GET_ALTERNATE_MODES': 'GET_ALTERNATE_MODES',
        'GET_CAM_SUPPORTED': 'GET_CAM_SUPPORTED',
        'GET_CURRENT_CAM': 'GET_CURRENT_CAM',
        'SET_NEW_CAM': 'SET_NEW_CAM',
        'SET_USB': 'SET_USB',
        'GET_PDOS': 'GET_PDOS',
        'GET_CABLE_PROPERTY': 'GET_CABLE_PROPERTY',
        'GET_CONNECTOR_STATUS': 'GET_CONNECTOR_STATUS',
        'GET_ERROR_STATUS': 'GET_ERROR_STATUS',
        'SET_POWER_LEVEL': 'SET_POWER_LEVEL',
        'GET_PD_MESSAGE': 'GET_PD_MESSAGE',
        'GET_ATTENTION_VDO': 'GET_ATTENTION_VDO',
        'GET_CAM_CS': 'GET_CAM_CS',
        'LPM_FW_UPDATE_REQUEST': 'LPM_FW_UPDATE_REQUEST',
        'SECURITY_REQUEST': 'SECURITY_REQUEST',
        'SET_RETIMER_MODE': 'SET_RETIMER_MODE',
        'SET_SINK_PATH': 'SET_SINK_PATH',
        'CHUNKING_SUPPORT': 'CHUNKING_SUPPORT',
        'SET_PDO': 'SET_PDOS',  // Backend uses SET_PDO, but spec is SET_PDOS
        'SET_PDOS': 'SET_PDOS',
        'VENDOR_DEFINED_COMMAND': 'VENDOR_DEFINED_COMMAND',
        'GET_LPM_PPM_INFO': 'GET_LPM_PPM_INFO',
        'READ_POWER_LEVEL': 'READ_POWER_LEVEL'
    };
    
    // Try to match command name
    for (const [key, value] of Object.entries(mapping)) {
        if (cmdName.toUpperCase().includes(key)) {
            return value;
        }
    }
    
    return null;
}

// Show command tooltip
function showCommandTooltip(commandElement, event) {
    const commandName = commandElement.dataset.cmdKey;
    const cmdKey = getCommandKey(commandName);
    
    if (!cmdKey || !COMMAND_APPLICABILITY[cmdKey]) {
        return; // No applicability data for this command
    }
    
    const applicability = COMMAND_APPLICABILITY[cmdKey];
    
    let html = `<div class="tooltip-title">Command Applicability</div>`;
    
    // Show OPM, PPM, LPM status
    html += `<div class="tooltip-row">`;
    html += `<span class="tooltip-label">OPM:</span>`;
    html += `<span class="tooltip-value ${applicability.OPM}">${applicability.OPM} - ${APPLICABILITY_LEGEND[applicability.OPM]}</span>`;
    html += `</div>`;
    
    html += `<div class="tooltip-row">`;
    html += `<span class="tooltip-label">PPM:</span>`;
    html += `<span class="tooltip-value ${applicability.PPM}">${applicability.PPM} - ${APPLICABILITY_LEGEND[applicability.PPM]}</span>`;
    html += `</div>`;
    
    html += `<div class="tooltip-row">`;
    html += `<span class="tooltip-label">LPM:</span>`;
    html += `<span class="tooltip-value ${applicability.LPM}">${applicability.LPM} - ${APPLICABILITY_LEGEND[applicability.LPM]}</span>`;
    html += `</div>`;
    
    // Add note if available
    if (applicability.note) {
        html += `<div class="tooltip-note">${applicability.note}</div>`;
    }
    
    tooltipElement.innerHTML = html;
    tooltipElement.classList.add('show');
    positionTooltip(event);
}

// Position tooltip
function positionTooltip(event) {
    if (!tooltipElement || !tooltipElement.classList.contains('show')) return;
    
    const tooltipRect = tooltipElement.getBoundingClientRect();
    const offset = 15;
    
    let left = event.pageX + offset;
    let top = event.pageY + offset;
    
    // Prevent tooltip from going off screen
    if (left + tooltipRect.width > window.innerWidth) {
        left = event.pageX - tooltipRect.width - offset;
    }
    
    if (top + tooltipRect.height > window.innerHeight + window.scrollY) {
        top = event.pageY - tooltipRect.height - offset;
    }
    
    tooltipElement.style.left = left + 'px';
    tooltipElement.style.top = top + 'px';
}

// Hide command tooltip
function hideCommandTooltip() {
    if (tooltipElement) {
        tooltipElement.classList.remove('show');
    }
}

// Select port
function selectPort(port) {
    // Don't allow selecting disabled ports
    const targetBtn = Array.from(portButtons).find(btn => parseInt(btn.dataset.port) === port);
    if (targetBtn && targetBtn.disabled) {
        return;
    }
    
    selectedPort = port;
    
    // Update UI - maintain 'enabled' class, just change 'active'
    portButtons.forEach(btn => {
        const portNum = parseInt(btn.dataset.port);
        if (portNum === port) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    // Update command hex if command is selected
    if (selectedCommand) {
        updateCommandHex();
    }
}

function getMaxVisiblePorts() {
    const uiPortButtons = document.querySelectorAll('.port-btn[data-port]');
    return uiPortButtons.length || 4;
}

// Extract port count from GET_CAPABILITY response and enable ports
function extractAndEnablePorts(decodedData, hexResponse) {
    try {
        let portCount = 0;
        
        // Try to extract from decoded data first - try multiple possible field names
        if (decodedData && decodedData['bNumConnectors']) {
            portCount = parseInt(decodedData['bNumConnectors']);
        } 
        // Fallback: parse from raw hex (byte 4 bits 0-6 contains number of connectors)
        else if (hexResponse) {
            const cleanHex = hexResponse.replace(/[^0-9a-fA-F]/g, '');
            if (cleanHex.length >= 10) {
                // Byte 4 (index 8-9) contains number of connectors in bits 0-6
                const byte4 = cleanHex.substring(8, 10);
                const byte4Value = parseInt(byte4, 16);
                portCount = byte4Value & 0x7F;  // Extract bits 0-6 (mask with 0x7F)
            }
        }
        
        if (portCount > 0) {
            const maxVisiblePorts = getMaxVisiblePorts();
            numDetectedPorts = Math.min(portCount, maxVisiblePorts);
            updatePortButtonStates();
            if (portCount > maxVisiblePorts) {
                showNotification(`Detected ${portCount} port(s). Showing first ${maxVisiblePorts} in UI.`, 'warning');
            } else {
                showNotification(`Detected ${portCount} port(s) - enabled in UI`, 'success');
            }
        }
    } catch (error) {
        console.error('Error extracting port count:', error);
    }
}

// Update port button states based on detected ports
function updatePortButtonStates() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    
    portButtons.forEach(btn => {
        const portNum = parseInt(btn.dataset.port);
        
        // Remove all state classes first
        btn.classList.remove('enabled', 'active');
        
        if (numDetectedPorts === 0) {
            // No ports detected yet - disable all ports
            btn.disabled = true;
        } else if (portNum <= numDetectedPorts) {
            // Enable detected ports with green color
            btn.disabled = false;
            btn.classList.add('enabled');
            if (portNum === selectedPort) {
                btn.classList.add('active');
            }
        } else {
            // Disable ports beyond detected count - gray and disabled
            btn.disabled = true;
        }
    });
    
    // Update filter buttons in pie chart section
    filterButtons.forEach(btn => {
        const filterValue = btn.dataset.filter;
        
        if (filterValue === 'all') {
            // 'All Ports' button is always enabled
            btn.disabled = false;
        } else {
            const portNum = parseInt(filterValue);
            if (numDetectedPorts === 0) {
                // No ports detected - disable all port filters
                btn.disabled = true;
            } else if (portNum <= numDetectedPorts) {
                // Enable filter for detected ports
                btn.disabled = false;
            } else {
                // Disable filter for non-existent ports
                btn.disabled = true;
                // If this was the active filter, switch to 'All Ports'
                if (btn.classList.contains('active')) {
                    btn.classList.remove('active');
                    const allBtn = document.querySelector('.filter-btn[data-filter="all"]');
                    if (allBtn) {
                        allBtn.classList.add('active');
                        currentViewPort = 'all';
                        updateResultsChart();
                    }
                }
            }
        }
    });
    
    // Update Run Command button state
    updateRunCommandButton();
}

// Update Run Command button state based on port detection and command selection
function updateRunCommandButton() {
    if (!runCommandBtn) return;
    
    if (numDetectedPorts === 0) {
        // No ports detected - disable Run Command
        runCommandBtn.disabled = true;
        runCommandBtn.title = 'Run GET_CAPABILITY first to detect ports';
    } else if (selectedCommand) {
        // Ports detected and command selected - enable
        runCommandBtn.disabled = false;
        runCommandBtn.title = 'Execute the selected command';
    } else {
        // Ports detected but no command selected
        runCommandBtn.disabled = true;
        runCommandBtn.title = 'Select a command first';
    }
}

// Update command hex display
async function updateCommandHex() {
    if (!selectedCommand) {
        commandHexInput.value = '';
        commandHexInput.dataset.rawHex = '';
        return;
    }
    
    try {
        const response = await fetch('/api/format_command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                command_key: selectedCommand,
                port: selectedPort,
                aardvark_mode: aardvarkMode
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Use the full_command from the API response which handles both modes (display)
            commandHexInput.value = data.full_command;
            // Store the raw hex for command execution
            commandHexInput.dataset.rawHex = data.ucsi_command;
        }
    } catch (error) {
        console.error('Error formatting command:', error);
    }
}

// Select command
function selectCommand(element) {
    // Remove previous selection
    document.querySelectorAll('.command-item').forEach(item => {
        item.classList.remove('selected');
    });

    // Add selection
    element.classList.add('selected');
    selectedCommand = element.dataset.cmdKey;
    selectedCommandInput.value = selectedCommand;
    
    // Update Run button based on port detection
    updateRunCommandButton();
    
    // Update command hex
    updateCommandHex();
}

// Switch tab
function switchTab(button) {
    // Update active tab
    tabButtons.forEach(btn => btn.classList.remove('active'));
    button.classList.add('active');

    const category = button.dataset.category;
    const commandItems = document.querySelectorAll('.command-item');

    commandItems.forEach(item => {
        if (category === 'all') {
            item.style.display = 'flex';
        } else {
            if (item.dataset.category === category) {
                item.style.display = 'flex';
            } else {
                item.style.display = 'none';
            }
        }
    });
}

// Filter commands
function filterCommands(searchTerm) {
    const commandItems = document.querySelectorAll('.command-item');
    const term = searchTerm.toLowerCase();

    commandItems.forEach(item => {
        const name = item.querySelector('.command-name').textContent.toLowerCase();
        const hex = item.querySelector('.command-hex').textContent.toLowerCase();

        if (name.includes(term) || hex.includes(term)) {
            item.style.display = 'flex';
        } else {
            item.style.display = 'none';
        }
    });
}

// Decode response
async function decodeResponse() {
    const hexResponse = hexResponseInput.value.trim();

    if (!hexResponse) {
        showNotification('Please enter hex response data', 'error');
        return;
    }

    if (!selectedCommand) {
        showNotification('Please select a command first', 'error');
        return;
    }

    // Show loading
    showLoading(true);

    try {
        const response = await fetch('/api/decode', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                hex_response: hexResponse,
                command_key: selectedCommand,
                ucsi_version: detectedVersion || '3.0',
                port: selectedPort
            })
        });

        const data = await response.json();

        if (data.success) {
            displayDecodedResult(data.decoded);
            currentDecodedResult = data.decoded;
            addToHistory(selectedCommand, hexResponse, data.decoded, selectedPort);
            showNotification('Decode successful!', 'success');
            
            // Check if this is GET_CAPABILITY and extract port count
            if (selectedCommand && selectedCommand.includes('GET_CAPABILITY')) {
                extractAndEnablePorts(data.decoded, hexResponse);
            }
            
            // Show save/copy buttons and update text
            updateSaveButtonText();
            if (saveResultBtn) saveResultBtn.style.display = 'inline-block';
            if (copyResultBtn) copyResultBtn.style.display = 'inline-block';
        } else {
            showNotification('Decode failed: ' + data.error, 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
        console.error('Decode error:', error);
    } finally {
        showLoading(false);
    }
}

// Display decoded result
function displayDecodedResult(decoded) {
    let html = '';
    
    // Check if this is an optional command that's not available
    if (decoded.status_override && decoded.status_override.includes('N/A')) {
        html += '<div class="decoded-section" style="background: #e8f4f8; padding: 16px; border-radius: 8px; border-left: 4px solid #0066cc; margin-bottom: 15px;">';
        html += '<div class="decoded-field" style="display: flex; align-items: center; gap: 12px;">';
        html += '<span class="field-label" style="font-size: 16px; font-weight: bold; color: #004080;">ℹ️ Status:</span>';
        html += '<span class="field-value" style="color: #004080; font-weight: bold; font-size: 18px;">' + escapeHtml(decoded.status_override) + '</span>';
        html += '</div>';
        if (decoded.optional_info) {
            html += '<div class="decoded-field" style="margin-top: 10px; padding: 10px; background: #fff; border-radius: 4px;">';
            html += '<span class="field-label" style="color: #004080;">Info:</span>';
            html += '<span class="field-value" style="color: #004080;">' + escapeHtml(decoded.optional_info) + '</span>';
            html += '</div>';
        }
        html += '</div>';
    }

    // Metadata
    html += '<div class="decoded-section">';
    html += '<div class="decoded-field">';
    html += '<span class="field-label">Command:</span>';
    html += '<span class="field-value">' + escapeHtml(decoded.command) + '</span>';
    html += '</div>';
    
    html += '<div class="decoded-field">';
    html += '<span class="field-label">Port:</span>';
    html += '<span class="field-value">Port ' + selectedPort + '</span>';
    html += '</div>';

    if (decoded.timestamp) {
        html += '<div class="decoded-field">';
        html += '<span class="field-label">Timestamp:</span>';
        html += '<span class="field-value">' + new Date(decoded.timestamp).toLocaleString() + '</span>';
        html += '</div>';
    }
    
    // Display error message if present (e.g., ErrorIndicator set)
    if (decoded.error) {
        html += '<div class="decoded-field" style="margin-top: 10px; padding: 10px; background: #7f1d1d; border-radius: 4px; border: 2px solid #ef4444;">';
        html += '<span class="field-label" style="color: #fca5a5;">⚠️ Error:</span>';
        html += '<span class="field-value" style="color: #fca5a5; font-weight: bold;">' + escapeHtml(decoded.error) + '</span>';
        html += '</div>';
    }
    
    // Display warning message if present (e.g., cached/stale data)
    if (decoded.warning) {
        html += '<div class="decoded-field" style="margin-top: 10px; padding: 10px; background: #78350f; border-radius: 4px; border: 2px solid #f59e0b;">';
        html += '<span class="field-label" style="color: #fcd34d;">⚠️ Warning:</span>';
        html += '<span class="field-value" style="color: #fcd34d;">' + escapeHtml(decoded.warning) + '</span>';
        html += '</div>';
    }
    
    // Check if this is GET_ALTERNATE_MODES and capture the modes
    if (decoded.command && decoded.command.includes('GET_ALTERNATE_MODES') && decoded.alternate_modes) {
        console.log('Detected GET_ALTERNATE_MODES response, storing alternate modes:', decoded.alternate_modes);
        detectedAlternateModes = decoded.alternate_modes;
    }

    // Check if we have raw_hex (normal case) or if this is MESSAGE_IN empty case
    if (decoded.raw_hex) {
        html += '<div class="decoded-field">';
        html += '<span class="field-label">Raw Length:</span>';
        html += '<span class="field-value">' + decoded.raw_len + ' bytes</span>';
        html += '</div>';

        html += '<div class="decoded-field">';
        html += '<span class="field-label">UCSI MESSAGE_IN:</span>';
        html += '<pre class="field-value" style="margin: 0; font-family: monospace; white-space: pre;">' + escapeHtml(decoded.raw_hex) + '</pre>';
        html += '</div>';
    } else if (decoded.status || decoded.message) {
        // MESSAGE_IN is empty case - show status/message
        if (decoded.status) {
            html += '<div class="decoded-field">';
            html += '<span class="field-label">Status:</span>';
            html += '<span class="field-value" style="color: #10b981;">' + escapeHtml(decoded.status) + '</span>';
            html += '</div>';
        }
        if (decoded.message) {
            html += '<div class="decoded-field">';
            html += '<span class="field-label">Message:</span>';
            html += '<span class="field-value">' + escapeHtml(decoded.message) + '</span>';
            html += '</div>';
        }
    }

    html += '</div>';
    
    // Display UCSI sections if available (when MESSAGE_IN is empty)
    if (decoded.UCSI_CONTROL || decoded.UCSI_VERSION || decoded.UCSI_CCI) {
        html += '<hr style="margin: 20px 0; border-color: #374151;">';
        html += '<div class="decoded-section" style="background: #1e293b; padding: 12px; border-radius: 8px; margin-bottom: 10px;">';
        html += '<h3 style="color: #60a5fa; margin-top: 0; margin-bottom: 12px; font-size: 16px;">UCSI Register Details</h3>';
        
        if (decoded.UCSI_CONTROL) {
            const trimmedControl = decoded.UCSI_CONTROL.trim();
            html += '<pre style="margin: 0 0 8px 0; font-family: monospace; white-space: pre-wrap; background: #0f172a; padding: 10px; border-radius: 4px; color: #e2e8f0; line-height: 1.5; border-left: 3px solid #3b82f6;">' + escapeHtml(trimmedControl) + '</pre>';
        }
        
        if (decoded.UCSI_VERSION) {
            const trimmedVersion = decoded.UCSI_VERSION.trim();
            html += '<pre style="margin: 0 0 8px 0; font-family: monospace; white-space: pre-wrap; background: #0f172a; padding: 10px; border-radius: 4px; color: #e2e8f0; line-height: 1.5; border-left: 3px solid #3b82f6;">' + escapeHtml(trimmedVersion) + '</pre>';
        }
        
        if (decoded.UCSI_CCI) {
            const trimmedCci = decoded.UCSI_CCI.trim();
            html += '<pre style="margin: 0; font-family: monospace; white-space: pre-wrap; background: #0f172a; padding: 10px; border-radius: 4px; color: #e2e8f0; line-height: 1.5; border-left: 3px solid #3b82f6;">' + escapeHtml(trimmedCci) + '</pre>';
        }
        
        html += '</div>';
    }

    // Display ErrorIndicator prominently if present
    if (decoded.hasOwnProperty('ErrorIndicator')) {
        const errorValue = String(decoded.ErrorIndicator).trim();
        const isZero = errorValue === '0' || errorValue === '0x00' || errorValue === '0x0000';
        const color = isZero ? '#10b981' : '#ef4444'; // green if 0, red otherwise
        const statusText = isZero ? '✓ No Error' : '✗ Error Detected';
        
        html += '<hr style="margin: 20px 0; border-color: #374151;">';
        html += '<div class="decoded-section" style="background: ' + (isZero ? '#064e3b' : '#7f1d1d') + '; padding: 16px; border-radius: 8px; margin-bottom: 10px; border: 2px solid ' + color + ';">';
        html += '<div class="decoded-field" style="display: flex; align-items: center; gap: 12px;">';
        html += '<span class="field-label" style="font-size: 16px; font-weight: bold; color: ' + color + ';">Command Result:</span>';
        html += '<span class="field-value" style="color: ' + color + '; font-weight: bold; font-size: 20px;">' + statusText + '</span>';
        html += '<span class="field-value" style="color: ' + color + '; font-weight: normal; font-size: 14px;">(ErrorIndicator: ' + errorValue + ')</span>';
        html += '</div>';
        html += '</div>';
    }
    
    // Display SET_POWER_LEVEL workflow comparison if present
    if (decoded.workflow_comparison && decoded.workflow_comparison.details) {
        html += '<hr style="margin: 20px 0; border-color: #374151;">';
        html += '<div class="decoded-section" style="background: #1e3a5f; padding: 16px; border-radius: 8px; margin-bottom: 10px; border: 2px solid #3b82f6;">';
        html += '<h3 style="color: #60a5fa; margin-top: 0; margin-bottom: 12px; font-size: 16px;">🔄 Before/After Comparison</h3>';
        
        const changes = decoded.workflow_comparison.details;
        const changedCount = Object.keys(changes).length;
        
        if (changedCount > 0) {
            html += '<p style="color: #fbbf24; font-weight: bold; margin-bottom: 12px;">⚠️ ' + changedCount + ' field(s) changed after SET_POWER_LEVEL</p>';
            html += '<div style="overflow-x: auto;">';
            html += '<table style="width: 100%; border-collapse: collapse; font-size: 13px;">';
            html += '<thead><tr style="background: #0f172a;">';
            html += '<th style="padding: 8px; border: 1px solid #4b5563; color: #60a5fa; text-align: left;">Field</th>';
            html += '<th style="padding: 8px; border: 1px solid #4b5563; color: #60a5fa; text-align: left;">Before</th>';
            html += '<th style="padding: 8px; border: 1px solid #4b5563; color: #60a5fa; text-align: left;">After</th>';
            html += '</tr></thead><tbody>';
            
            for (const [fieldName, change] of Object.entries(changes)) {
                html += '<tr style="background: #1e293b;">';
                html += '<td style="padding: 8px; border: 1px solid #4b5563; color: #fbbf24; font-weight: bold;">' + escapeHtml(formatFieldName(fieldName)) + '</td>';
                html += '<td style="padding: 8px; border: 1px solid #4b5563; color: #94a3b8;">' + escapeHtml(String(change.before)) + '</td>';
                html += '<td style="padding: 8px; border: 1px solid #4b5563; color: #10b981; font-weight: bold; background: #064e3b;">' + escapeHtml(String(change.after)) + '</td>';
                html += '</tr>';
            }
            
            html += '</tbody></table>';
            html += '</div>';
        } else {
            html += '<p style="color: #94a3b8;">ℹ️ No changes detected in connector status</p>';
        }
        
        html += '</div>';
    }

    // Display GET_CONNECTOR_STATUS with highlighted changes (for SET_POWER_LEVEL)
    if (decoded.connector_status_after && decoded.workflow_comparison) {
        html += '<hr style="margin: 20px 0; border-color: #374151;">';
        html += '<div class="decoded-section" style="background: #1e293b; padding: 16px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #10b981;">';
        html += '<h3 style="color: #10b981; margin-top: 0; margin-bottom: 12px; font-size: 16px;">📊 GET_CONNECTOR_STATUS (After SET_POWER_LEVEL)</h3>';
        html += '<p style="color: #94a3b8; font-size: 13px; margin-bottom: 12px;">Fields with changes are highlighted in yellow</p>';
        
        const statusAfter = decoded.connector_status_after;
        const changes = decoded.workflow_comparison.details || {};
        
        // Display fields from connector_status_after
        for (const [key, value] of Object.entries(statusAfter)) {
            // Skip metadata fields
            if (['command', 'timestamp', 'raw_len', 'raw_hex', 'fields', 'error', 'warning'].includes(key)) {
                continue;
            }
            
            const isChanged = changes.hasOwnProperty(key);
            const bgColor = isChanged ? '#422006' : 'transparent';  // dark yellow background for changed fields
            const labelColor = isChanged ? '#fbbf24' : '#60a5fa';   // yellow for changed, blue for unchanged
            const valueColor = isChanged ? '#10b981' : '#e2e8f0';   // green for changed, white for unchanged
            const fontWeight = isChanged ? 'bold' : 'normal';
            
            html += '<div class="decoded-field" style="background: ' + bgColor + '; padding: 8px; border-radius: 4px; margin-bottom: 4px;">';
            html += '<span class="field-label" style="color: ' + labelColor + '; font-weight: ' + fontWeight + ';">' + formatFieldName(key) + ':</span>';
            
            if (Array.isArray(value)) {
                html += '<div class="field-array">';
                if (value.length === 0) {
                    html += '<span class="field-value" style="color: ' + valueColor + ';">[]</span>';
                } else if (typeof value[0] === 'object') {
                    value.forEach((obj, index) => {
                        html += '<div style="margin: 10px 0; padding: 10px; background: #374151; border-radius: 4px;">';
                        html += '<strong>' + (obj.Type || 'Item ' + (index + 1)) + '</strong><br>';
                        for (const [k, v] of Object.entries(obj)) {
                            if (k !== 'Type') {
                                html += formatFieldName(k) + ': <span class="field-value" style="color: ' + valueColor + ';">' + escapeHtml(String(v)) + '</span><br>';
                            }
                        }
                        html += '</div>';
                    });
                } else {
                    html += '<span class="field-value" style="color: ' + valueColor + ';">' + value.join(', ') + '</span>';
                }
                html += '</div>';
            } else if (typeof value === 'object' && value !== null) {
                html += '<div class="field-array">';
                for (const [k, v] of Object.entries(value)) {
                    html += formatFieldName(k) + ': <span class="field-value" style="color: ' + valueColor + ';">' + escapeHtml(String(v)) + '</span><br>';
                }
                html += '</div>';
            } else {
                html += '<span class="field-value" style="color: ' + valueColor + '; font-weight: ' + fontWeight + ';">' + escapeHtml(String(value)) + '</span>';
            }
            
            html += '</div>';
        }
        
        html += '</div>';
    }

    // Decoded fields
    html += '<hr style="margin: 20px 0; border-color: #374151;">';
    html += '<div class="decoded-section">';

    for (const [key, value] of Object.entries(decoded)) {
        // Skip metadata fields and UCSI sections
        if (['command', 'timestamp', 'raw_len', 'raw_hex', 'status', 'message', 'UCSI_CONTROL', 'UCSI_VERSION', 'UCSI_CCI', 'fields', 'ErrorIndicator', 'optional_info', 'status_override', 'workflow_comparison', 'workflow_summary', 'connector_status_before', 'connector_status_after', 'error', 'warning'].includes(key)) {
            continue;
        }

        html += '<div class="decoded-field">';
        html += '<span class="field-label">' + formatFieldName(key) + ':</span>';

        if (Array.isArray(value)) {
            html += '<div class="field-array">';
            if (value.length === 0) {
                html += '<span class="field-value">[]</span>';
            } else if (typeof value[0] === 'object') {
                // Array of objects (like PDOs)
                value.forEach((obj, index) => {
                    html += '<div style="margin: 10px 0; padding: 10px; background: #374151; border-radius: 4px;">';
                    html += '<strong>' + (obj.Type || 'Item ' + (index + 1)) + '</strong><br>';
                    for (const [k, v] of Object.entries(obj)) {
                        if (k !== 'Type') {
                            html += formatFieldName(k) + ': <span class="field-value">' + escapeHtml(String(v)) + '</span><br>';
                        }
                    }
                    html += '</div>';
                });
            } else {
                // Simple array
                html += '<span class="field-value">' + value.join(', ') + '</span>';
            }
            html += '</div>';
        } else if (typeof value === 'object' && value !== null) {
            html += '<div class="field-array">';
            for (const [k, v] of Object.entries(value)) {
                html += formatFieldName(k) + ': <span class="field-value">' + escapeHtml(String(v)) + '</span><br>';
            }
            html += '</div>';
        } else {
            // Special styling for ErrorIndicator
            if (key === 'ErrorIndicator' || key === 'error_indicator') {
                const errorValue = String(value).trim();
                const isZero = errorValue === '0' || errorValue === '0x00' || errorValue === '0x0000';
                const color = isZero ? '#10b981' : '#ef4444'; // green if 0, red otherwise
                html += '<span class="field-value" style="color: ' + color + '; font-weight: bold; font-size: 16px;">' + escapeHtml(String(value)) + '</span>';
            } else {
                html += '<span class="field-value">' + escapeHtml(String(value)) + '</span>';
            }
        }

        html += '</div>';
    }
    
    // Display hierarchical table if 'fields' array exists (e.g., GET_CAPABILITY)
    if (decoded.fields && Array.isArray(decoded.fields)) {
        console.log('Rendering hierarchical table with', decoded.fields.length, 'fields');
        html += '<div style="overflow-x: auto; margin-top: 20px;">';
        html += '<table style="width: 100%; border-collapse: collapse; font-family: monospace; font-size: 13px; color: #e2e8f0;">';
        html += '<thead><tr style="background: #374151;">';
        html += '<th style="padding: 10px; text-align: left; border: 1px solid #4b5563; color: #f3f4f6;">Offset (Bits)</th>';
        html += '<th style="padding: 10px; text-align: left; border: 1px solid #4b5563; color: #f3f4f6;">Field</th>';
        html += '<th style="padding: 10px; text-align: left; border: 1px solid #4b5563; color: #f3f4f6;">Size (Bits)</th>';
        html += '<th style="padding: 10px; text-align: left; border: 1px solid #4b5563; color: #f3f4f6;">Value</th>';
        html += '</tr></thead><tbody>';
        
        decoded.fields.forEach(field => {
            // Main field row
            html += '<tr style="background: #1e293b;">';
            html += '<td style="padding: 8px; border: 1px solid #4b5563; color: #e2e8f0;">' + (field.offset || '') + '</td>';
            html += '<td style="padding: 8px; border: 1px solid #4b5563; font-weight: bold; color: #fbbf24;">' + escapeHtml(field.field) + '</td>';
            html += '<td style="padding: 8px; border: 1px solid #4b5563; color: #e2e8f0;">' + (field.size || '') + '</td>';
            
            // Special styling for ErrorIndicator
            if (field.field === 'ErrorIndicator' || field.field === 'Error Indicator') {
                const errorValue = field.value.trim();
                const isZero = errorValue === '0' || errorValue === '0x00' || errorValue === '0x0000';
                const color = isZero ? '#10b981' : '#ef4444'; // green if 0, red otherwise
                html += '<td style="padding: 8px; border: 1px solid #4b5563; color: ' + color + '; font-weight: bold; font-size: 16px;">' + escapeHtml(field.value) + '</td>';
            } else {
                html += '<td style="padding: 8px; border: 1px solid #4b5563; color: #e2e8f0;">' + escapeHtml(field.value) + '</td>';
            }
            html += '</tr>';
            
            // Children (sub-fields)
            if (field.children && field.children.length > 0) {
                field.children.forEach(child => {
                    html += '<tr style="background: #0f172a;">';
                    html += '<td style="padding: 8px; border: 1px solid #4b5563; color: #e2e8f0;"></td>';
                    html += '<td style="padding: 8px 8px 8px 30px; border: 1px solid #4b5563; color: #e2e8f0;">→ ' + escapeHtml(child.field) + '</td>';
                    html += '<td style="padding: 8px; border: 1px solid #4b5563; color: #e2e8f0;"></td>';
                    html += '<td style="padding: 8px; border: 1px solid #4b5563; color: #10b981;">' + escapeHtml(child.value) + '</td>';
                    html += '</tr>';
                    
                    // Nested children (for bmPowerSource)
                    if (child.children && child.children.length > 0) {
                        child.children.forEach(nested => {
                            html += '<tr style="background: #020617;">';
                            html += '<td style="padding: 8px; border: 1px solid #4b5563; color: #e2e8f0;"></td>';
                            html += '<td style="padding: 8px 8px 8px 60px; border: 1px solid #4b5563; color: #e2e8f0;">⤷ ' + escapeHtml(nested.field) + '</td>';
                            html += '<td style="padding: 8px; border: 1px solid #4b5563; color: #e2e8f0;"></td>';
                            html += '<td style="padding: 8px; border: 1px solid #4b5563; color: #10b981;">' + escapeHtml(nested.value) + '</td>';
                            html += '</tr>';
                        });
                    }
                });
            }
        });
        
        html += '</tbody></table>';
        html += '</div>';
    } else {
        console.log('No fields array found in decoded data');
    }

    html += '</div>';

    html += '</div>';

    outputArea.innerHTML = html;
}

// Format field name
function formatFieldName(name) {
    // Convert snake_case and camelCase to Title Case
    // But preserve consecutive capitals (like PD, USB, BC, VDO, CCOM, VBUS)
    return name
        .replace(/_/g, ' ')
        // Only add space before capital if it's followed by lowercase
        // This preserves acronyms like PD, USB, BC, etc.
        .replace(/([A-Z])(?=[a-z])/g, ' $1')
        .replace(/^./, str => str.toUpperCase())
        .trim();
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Toggle dmesg logs visibility
function toggleDmesgLogs() {
    const content = document.getElementById('dmesgLogsContent');
    const toggle = document.getElementById('dmesgToggle');
    if (content && toggle) {
        if (content.style.display === 'none') {
            content.style.display = 'block';
            toggle.textContent = '▼';
        } else {
            content.style.display = 'none';
            toggle.textContent = '▶';
        }
    }
}

// Update Linux Logs section
function updateLinuxLogsSection(dmesgLogs) {
    const logsSection = document.getElementById('linuxLogsSection');
    const logsText = document.getElementById('dmesgLogsText');
    
    if (!logsSection || !logsText) {
        console.log('Linux logs section elements not found');
        return;
    }
    
    // Only show dmesg logs on Linux platform
    if (!platformInfo.is_linux) {
        console.log('Not Linux platform - hiding dmesg section');
        logsSection.style.display = 'none';
        return;
    }
    
    if (dmesgLogs) {
        // Show the section and populate with logs
        console.log('Showing Linux logs section with', dmesgLogs.length, 'characters');
        logsSection.style.display = 'block';
        logsText.textContent = dmesgLogs;
    } else {
        // Hide the section if no logs
        console.log('Hiding and clearing Linux logs section');
        logsSection.style.display = 'none';
        logsText.textContent = '';
        // Also reset the toggle to expanded state for next time
        const toggle = document.getElementById('dmesgToggle');
        if (toggle) {
            toggle.textContent = '▼';
        }
        const content = document.getElementById('dmesgLogsContent');
        if (content) {
            content.style.display = 'block';
        }
    }
}

// Show notification
function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = type === 'error' ? 'error-message' : 'success-message';
    notification.textContent = message;
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.minWidth = '300px';
    notification.style.animation = 'slideIn 0.3s ease';

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Show/hide loading overlay
function showLoading(show) {
    loadingOverlay.style.display = show ? 'flex' : 'none';
}

// Clear form
function clearForm() {
    hexResponseInput.value = '';
    currentDecodedResult = null;
    // Note: allDecodedResults is preserved for batch saving - clear manually if needed
    outputArea.innerHTML = `
        <div class="placeholder">
            <p>👈 Select a command and click Run to execute and decode</p>
            <p class="hint">Or enter hex response data manually</p>
        </div>
    `;
    
    // Clear Linux logs section
    updateLinuxLogsSection(null);
    
    // Hide save/copy buttons
    const saveResultBtnGroup = document.getElementById('saveResultBtnGroup');
    if (saveResultBtnGroup) saveResultBtnGroup.style.display = 'none';
    if (copyResultBtn) copyResultBtn.style.display = 'none';
}

// History management
function addToHistory(command, hex, decoded, port) {
    const historyItem = {
        id: Date.now(),
        command: command,
        hex: hex,
        decoded: decoded,
        port: port,
        timestamp: new Date().toISOString()
    };

    decodeHistory.unshift(historyItem);

    // Keep only last 20 items
    if (decodeHistory.length > 20) {
        decodeHistory = decodeHistory.slice(0, 20);
    }

    saveHistory();
    renderHistory();
}

function renderHistory() {
    if (decodeHistory.length === 0) {
        historyList.innerHTML = '<div style="padding: 20px; text-align: center; color: #64748b;">No history yet</div>';
        return;
    }

    let html = '';
    decodeHistory.forEach(item => {
        html += '<div class="history-item" data-id="' + item.id + '">';
        html += '<div class="history-command">' + escapeHtml(item.command) + ' (Port ' + (item.port || 1) + ')</div>';
        html += '<div class="history-hex">' + escapeHtml(item.hex.substring(0, 40)) + (item.hex.length > 40 ? '...' : '') + '</div>';
        html += '<div class="history-time">' + new Date(item.timestamp).toLocaleString() + '</div>';
        html += '</div>';
    });

    historyList.innerHTML = html;

    // Add click handlers to history items
    document.querySelectorAll('.history-item').forEach(item => {
        item.addEventListener('click', function() {
            loadHistoryItem(parseInt(this.dataset.id));
        });
    });
}

function loadHistoryItem(id) {
    const item = decodeHistory.find(h => h.id === id);
    if (item) {
        // Select port
        if (item.port) {
            selectPort(item.port);
        }
        
        // Select command
        const commandItems = document.querySelectorAll('.command-item');
        commandItems.forEach(cmdItem => {
            if (cmdItem.dataset.cmdKey === item.command) {
                selectCommand(cmdItem);
            }
        });

        // Load hex
        hexResponseInput.value = item.hex;

        // Display decoded result
        displayDecodedResult(item.decoded);

        showNotification('History item loaded', 'success');
    }
}

function saveHistory() {
    try {
        localStorage.setItem('ucsi_decode_history', JSON.stringify(decodeHistory));
    } catch (e) {
        console.error('Failed to save history:', e);
    }
}

function loadHistory() {
    try {
        const saved = localStorage.getItem('ucsi_decode_history');
        if (saved) {
            decodeHistory = JSON.parse(saved);
        }
    } catch (e) {
        console.error('Failed to load history:', e);
        decodeHistory = [];
    }
}

function clearHistory() {
    if (confirm('Are you sure you want to clear all history?')) {
        decodeHistory = [];
        allDecodedResults = []; // Also clear accumulated results
        saveHistory();
        renderHistory();
        updateSaveButtonText(); // Update save button text
        showNotification('History cleared', 'success');
    }
}

// Update save button text to show how many results are accumulated
function updateSaveButtonText() {
    if (!saveResultBtn) return;
    
    const count = allDecodedResults.length;
    if (count > 1) {
        saveResultBtn.innerHTML = `💾 Save Results (${count})`;
        saveResultBtn.title = `Save all ${count} command results to file`;
    } else if (count === 1) {
        saveResultBtn.innerHTML = '💾 Save Result';
        saveResultBtn.title = 'Save the command result to file';
    } else {
        saveResultBtn.innerHTML = '💾 Save Result';
        saveResultBtn.title = 'Save the current result to file';
    }
}

// Save current result to file
function saveCurrentResult() {
    // Check if we have accumulated results or just a single result
    let resultsToSave;
    if (allDecodedResults.length > 0) {
        resultsToSave = allDecodedResults;
    } else if (currentDecodedResult) {
        // Wrap single result in same structure as accumulated results
        resultsToSave = [{
            command: selectedCommand,
            port: selectedPort,
            timestamp: new Date().toLocaleString(),
            decoded: currentDecodedResult
        }];
    } else {
        resultsToSave = [];
    }
    
    if (resultsToSave.length === 0) {
        alert('No results to save. Please run a command first.');
        return;
    }
    
    const timestamp = new Date().toISOString().replace(/:/g, '-').split('.')[0];
    const filename = resultsToSave.length === 1 
        ? `UCSI_Decode_${resultsToSave[0].command.replace(/\s/g, '_')}_Port${resultsToSave[0].port}_${timestamp}.txt`
        : `UCSI_Decode_AllResults_${timestamp}.txt`;
    
    let content = '='.repeat(70) + '\n';
    content += 'UCSI DECODER - DECODED RESULTS\n';
    content += '='.repeat(70) + '\n\n';
    content += `Total Results: ${resultsToSave.length}\n`;
    content += `Generated: ${new Date().toLocaleString()}\n`;
    content += `UCSI Version: ${ucsiVersionSelect ? ucsiVersionSelect.value : detectedVersion}\n`;
    content += '\n';
    
    // Iterate through all results
    resultsToSave.forEach((result, index) => {
        content += '\n' + '='.repeat(70) + '\n';
        content += `RESULT #${index + 1}\n`;
        content += '='.repeat(70) + '\n\n';
        content += `Command: ${result.command}\n`;
        content += `Port: ${result.port}\n`;
        content += `Timestamp: ${result.timestamp}\n`;
        content += '\n' + '-'.repeat(70) + '\n';
        content += 'RAW DATA\n';
        content += '-'.repeat(70) + '\n';
        
        // Handle cases where raw_hex might not be present
        if (result.decoded.raw_hex) {
            content += `Length: ${result.decoded.raw_len || 'N/A'} bytes\n`;
            content += `Hex: ${result.decoded.raw_hex}\n`;
        } else if (result.decoded.status || result.decoded.message) {
            content += `Status: ${result.decoded.status || 'N/A'}\n`;
            if (result.decoded.message) {
                content += `Message: ${result.decoded.message}\n`;
            }
        }
        
        // Include UCSI sections if available
        if (result.decoded.UCSI_CONTROL || result.decoded.UCSI_VERSION || result.decoded.UCSI_CCI) {
            content += '\n' + '-'.repeat(70) + '\n';
            content += 'UCSI SECTIONS\n';
            content += '-'.repeat(70) + '\n\n';
            
            if (result.decoded.UCSI_CONTROL) {
                content += 'UCSI_CONTROL:\n';
                content += result.decoded.UCSI_CONTROL.trim() + '\n\n';
            }
            
            if (result.decoded.UCSI_VERSION) {
                content += 'UCSI_VERSION:\n';
                content += result.decoded.UCSI_VERSION.trim() + '\n\n';
            }
            
            if (result.decoded.UCSI_CCI) {
                content += 'UCSI_CCI:\n';
                content += result.decoded.UCSI_CCI.trim() + '\n\n';
            }
        }
        
        content += '\n' + '-'.repeat(70) + '\n';
        content += 'DECODED FIELDS\n';
        content += '-'.repeat(70) + '\n\n';
        
        content += formatDecodedForText(result.decoded);
    });
    
    downloadTextFile(content, filename);
    showNotification(`Result${resultsToSave.length > 1 ? 's' : ''} saved: ${filename}`, 'success');
}

// Save only the last (most recent) individual command result as text
function saveLastResult() {
    if (!currentDecodedResult) {
        alert('No result to save. Please run a command first.');
        return;
    }
    
    const result = {
        command: selectedCommand,
        port: selectedPort,
        timestamp: new Date().toLocaleString(),
        decoded: currentDecodedResult
    };
    
    const timestamp = new Date().toISOString().replace(/:/g, '-').split('.')[0];
    const filename = `UCSI_Decode_${result.command.replace(/\s/g, '_')}_Port${result.port}_${timestamp}.txt`;
    
    let content = '='.repeat(70) + '\n';
    content += 'UCSI DECODER - DECODED RESULT\n';
    content += '='.repeat(70) + '\n\n';
    content += `Generated: ${new Date().toLocaleString()}\n`;
    content += `UCSI Version: ${ucsiVersionSelect ? ucsiVersionSelect.value : detectedVersion}\n`;
    content += '\n';
    
    content += '\n' + '='.repeat(70) + '\n';
    content += `Command: ${result.command}\n`;
    content += `Port: ${result.port}\n`;
    content += `Timestamp: ${result.timestamp}\n`;
    content += '='.repeat(70) + '\n\n';
    
    content += '-'.repeat(70) + '\n';
    content += 'RAW DATA\n';
    content += '-'.repeat(70) + '\n';
    
    if (result.decoded.raw_hex) {
        content += `Length: ${result.decoded.raw_len || 'N/A'} bytes\n`;
        content += `Hex: ${result.decoded.raw_hex}\n`;
    } else if (result.decoded.status || result.decoded.message) {
        content += `Status: ${result.decoded.status || 'N/A'}\n`;
        if (result.decoded.message) {
            content += `Message: ${result.decoded.message}\n`;
        }
    }
    
    if (result.decoded.UCSI_CONTROL || result.decoded.UCSI_VERSION || result.decoded.UCSI_CCI) {
        content += '\n' + '-'.repeat(70) + '\n';
        content += 'UCSI SECTIONS\n';
        content += '-'.repeat(70) + '\n\n';
        
        if (result.decoded.UCSI_CONTROL) {
            content += 'UCSI_CONTROL:\n';
            content += result.decoded.UCSI_CONTROL.trim() + '\n\n';
        }
        if (result.decoded.UCSI_VERSION) {
            content += 'UCSI_VERSION:\n';
            content += result.decoded.UCSI_VERSION.trim() + '\n\n';
        }
        if (result.decoded.UCSI_CCI) {
            content += 'UCSI_CCI:\n';
            content += result.decoded.UCSI_CCI.trim() + '\n\n';
        }
    }
    
    content += '\n' + '-'.repeat(70) + '\n';
    content += 'DECODED FIELDS\n';
    content += '-'.repeat(70) + '\n\n';
    content += formatDecodedForText(result.decoded);
    
    downloadTextFile(content, filename);
    showNotification(`Last result saved: ${filename}`, 'success');
}

// Save only the last (most recent) individual command result as PDF
function saveLastResultPDF() {
    if (!currentDecodedResult) {
        alert('No result to save. Please run a command first.');
        return;
    }
    
    if (typeof jspdf === 'undefined') {
        alert('PDF library not loaded. Please refresh the page and try again.');
        return;
    }
    
    // Wrap single result in the same structure saveCurrentResultPDF expects
    const singleResult = [{
        command: selectedCommand,
        port: selectedPort,
        timestamp: new Date().toLocaleString(),
        decoded: currentDecodedResult
    }];
    
    // Temporarily replace allDecodedResults to reuse saveCurrentResultPDF logic
    const savedAll = allDecodedResults;
    allDecodedResults = singleResult;
    saveCurrentResultPDF();
    allDecodedResults = savedAll;
}

// Copy current result to clipboard
function copyCurrentResult() {
    if (!currentDecodedResult) {
        showNotification('No result to copy', 'error');
        return;
    }
    
    let content = `Command: ${selectedCommand}\n`;
    content += `Port: ${selectedPort}\n`;
    content += `Timestamp: ${new Date().toLocaleString()}\n\n`;
    
    // Include raw data if available
    if (currentDecodedResult.raw_hex) {
        content += `Raw Hex: ${currentDecodedResult.raw_hex}\n`;
        content += `Length: ${currentDecodedResult.raw_len || 'N/A'} bytes\n\n`;
    } else if (currentDecodedResult.status || currentDecodedResult.message) {
        content += `Status: ${currentDecodedResult.status || 'N/A'}\n`;
        if (currentDecodedResult.message) {
            content += `Message: ${currentDecodedResult.message}\n`;
        }
        content += '\n';
    }
    
    // Include UCSI sections if available
    if (currentDecodedResult.UCSI_CONTROL || currentDecodedResult.UCSI_VERSION || currentDecodedResult.UCSI_CCI) {
        content += 'UCSI Sections:\n';
        content += '-'.repeat(50) + '\n';
        
        if (currentDecodedResult.UCSI_CONTROL) {
            content += currentDecodedResult.UCSI_CONTROL.trim() + '\n\n';
        }
        
        if (currentDecodedResult.UCSI_VERSION) {
            content += currentDecodedResult.UCSI_VERSION.trim() + '\n\n';
        }
        
        if (currentDecodedResult.UCSI_CCI) {
            content += currentDecodedResult.UCSI_CCI.trim() + '\n\n';
        }
    }
    
    content += 'Decoded Fields:\n';
    content += '-'.repeat(50) + '\n';
    content += formatDecodedForText(currentDecodedResult);
    
    navigator.clipboard.writeText(content).then(() => {
        showNotification('Result copied to clipboard', 'success');
    }).catch(err => {
        showNotification('Failed to copy: ' + err, 'error');
    });
}

// Export history summary
function exportHistorySummary() {
    if (decodeHistory.length === 0) {
        showNotification('No history to export', 'error');
        return;
    }
    
    const timestamp = new Date().toISOString().replace(/:/g, '-').split('.')[0];
    const filename = `UCSI_Summary_${timestamp}.txt`;
    
    let content = '='.repeat(70) + '\n';
    content += 'UCSI DECODER - DECODE HISTORY SUMMARY\n';
    content += '='.repeat(70) + '\n\n';
    content += `Export Date: ${new Date().toLocaleString()}\n`;
    content += `Total Decodes: ${decodeHistory.length}\n`;
    content += '\n' + '='.repeat(70) + '\n\n';
    
    decodeHistory.forEach((item, index) => {
        content += `[${index + 1}] ${item.command} - Port ${item.port || 1}\n`;
        content += '-'.repeat(70) + '\n';
        content += `Time: ${new Date(item.timestamp).toLocaleString()}\n`;
        content += `Hex Response: ${item.hex}\n`;
        content += `\nDecoded:\n`;
        content += formatDecodedForText(item.decoded, '  ');
        content += '\n' + '='.repeat(70) + '\n\n';
    });
    
    downloadTextFile(content, filename);
    showNotification('Summary exported: ' + filename, 'success');
}

// Format decoded result for text output
function formatDecodedForText(decoded, indent = '') {
    let text = '';
    
    // Add ErrorIndicator prominently if present
    if (decoded.hasOwnProperty('ErrorIndicator')) {
        const errorValue = String(decoded.ErrorIndicator).trim();
        const isZero = errorValue === '0' || errorValue === '0x00' || errorValue === '0x0000';
        const statusText = isZero ? 'No Error' : 'Error Detected';
        text += `${indent}Error Indicator: ${errorValue} (${statusText})\n\n`;
    }
    
    // Process all fields including arrays and objects
    for (const [key, value] of Object.entries(decoded)) {
        // Skip metadata fields and UCSI sections (these are handled separately in saveCurrentResult)
        if (['command', 'timestamp', 'raw_len', 'raw_hex', 'status', 'message', 'UCSI_CONTROL', 'UCSI_VERSION', 'UCSI_CCI', 'ErrorIndicator', 'error', 'warning'].includes(key)) {
            continue;
        }
        
        const label = formatFieldName(key);
        
        // Handle 'fields' array specially for hierarchical table data
        if (key === 'fields' && Array.isArray(value)) {
            text += `${indent}${label} (Hierarchical Table):\n`;
            value.forEach((field, index) => {
                text += `${indent}  [${index + 1}] ${field.field}\n`;
                if (field.offset) text += `${indent}      Offset: ${field.offset}\n`;
                if (field.size) text += `${indent}      Size: ${field.size}\n`;
                text += `${indent}      Value: ${field.value}\n`;
                
                // Children (sub-fields)
                if (field.children && field.children.length > 0) {
                    field.children.forEach(child => {
                        text += `${indent}      → ${child.field}: ${child.value}\n`;
                        
                        // Nested children
                        if (child.children && child.children.length > 0) {
                            child.children.forEach(nested => {
                                text += `${indent}         ⤷ ${nested.field}: ${nested.value}\n`;
                            });
                        }
                    });
                }
            });
        }
        // Handle regular arrays
        else if (Array.isArray(value)) {
            text += `${indent}${label}:\n`;
            if (value.length === 0) {
                text += `${indent}  (empty)\n`;
            } else if (typeof value[0] === 'object') {
                value.forEach((obj, i) => {
                    text += `${indent}  [${i + 1}] ${obj.Type || 'Item'}\n`;
                    for (const [k, v] of Object.entries(obj)) {
                        if (k !== 'Type') {
                            text += `${indent}    ${formatFieldName(k)}: ${v}\n`;
                        }
                    }
                });
            } else {
                text += `${indent}  ${value.join(', ')}\n`;
            }
        } 
        // Handle objects
        else if (typeof value === 'object' && value !== null) {
            text += `${indent}${label}:\n`;
            for (const [k, v] of Object.entries(value)) {
                text += `${indent}  ${formatFieldName(k)}: ${v}\n`;
            }
        } 
        // Handle simple values
        else {
            text += `${indent}${label}: ${value}\n`;
        }
    }
    
    return text;
}

// Download text file
function downloadTextFile(content, filename) {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Add CSS animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Run Command Function
let dialogResolve = null;

function runCommand() {
    if (!selectedCommand) {
        alert('Please select a command first');
        return;
    }

    const cmdName = selectedCommand;
    
    // Check if command needs parameters
    if (cmdName.includes('CONNECTOR_RESET')) {
        showConnectorResetDialog();
    } else if (cmdName.includes('ACK_CC_CI')) {
        showAckCcCiDialog();
    } else if (cmdName.includes('SET_RETIMER_MODE')) {
        showRetimerModeDialog();
    } else if (cmdName.includes('SET_NOTIFICATION_ENABLE')) {
        showNotificationDialog();
    } else if (cmdName.includes('SET_POWER_LEVEL')) {
        const powerType = cmdName.includes('Source') ? 'source' : 'sink';
        showPowerLevelDialog(powerType);
    } else if (cmdName.includes('READ_POWER_LEVEL')) {
        showReadPowerLevelDialog();
    } else if (cmdName.includes('SET_UOR') && !cmdName.includes('(')) {
        showUorDialog();
    } else if (cmdName.includes('SET_PDR') && !cmdName.includes('(')) {
        showPdrDialog();
    } else if (cmdName.includes('GET_ALTERNATE_MODES')) {
        showAlternateModesDialog();
    } else if (cmdName.includes('SET_USB')) {
        showSetUsbDialog();
    } else if (cmdName.includes('SET_NEW_CAM')) {
        showSetNewCamDialog();
    } else if (cmdName.includes('VENDOR_DEFINED')) {
        // VENDOR_DEFINED requires the full 255-byte loopback payload — run the VDC test
        runVdcLoopbackTest();
    } else {
        // No parameters needed, execute command directly
        executeCommand();
    }
}

function executeCommand() {
    const cmdHexDisplay = commandHexInput.value;
    
    if (!cmdHexDisplay) {
        alert('Command hex is missing');
        return;
    }
    
    // Use the raw hex stored in the data attribute (platform-independent)
    let cmdHex = commandHexInput.dataset.rawHex || '';
    
    // Fallback: extract hex from display format if data attribute is missing
    if (!cmdHex) {
        cmdHex = cmdHexDisplay;
        // Remove Aardvark format: "Aardvark I2C: 09 08 XX XX XX..."
        if (cmdHexDisplay.includes('Aardvark I2C:')) {
            // Extract the command bytes after the 09 08 header
            const hexMatch = cmdHexDisplay.match(/Aardvark I2C:\s*09\s*08\s*(.+)/);
            if (hexMatch) {
                // Remove spaces and get the 8 command bytes
                cmdHex = hexMatch[1].replace(/\s+/g, '');
            }
        }
        // Remove Windows format: "UcsiControl.exe send <HighDW> <LowDW>" or "UcsiControl.exe send 0 <hex>"
        else if (cmdHexDisplay.includes('UcsiControl.exe send ')) {
            const parts = cmdHexDisplay.replace(/.*UcsiControl\.exe send\s+/i, '').trim().split(/\s+/);
            if (parts.length === 2) {
                // Two DWORDs: combine as <HighDW><LowDW>
                cmdHex = parts[0].padStart(8, '0') + parts[1].padStart(8, '0');
            } else {
                cmdHex = parts[parts.length - 1];
            }
        }
        // Remove Linux format: "echo 0x<hex> > command"
        else if (cmdHexDisplay.includes('echo 0x') && cmdHexDisplay.includes('> command')) {
            const match = cmdHexDisplay.match(/echo 0x([0-9a-fA-F]+)/);
            if (match) {
                cmdHex = match[1];
            }
        }
    }
    
    console.log('Original value:', cmdHexDisplay);
    console.log('Extracted hex:', cmdHex);
    
    // Clear Linux logs section before running new command
    updateLinuxLogsSection(null);
    
    // Show loading
    showLoading(true);
    outputArea.innerHTML = '<div style="padding: 20px; text-align: center;">⏳ Executing command...</div>';
    
    // Prepare payload
    const payload = {
        command_key: selectedCommand,
        command_hex: cmdHex,
        port: selectedPort,
        ucsi_version: detectedVersion,
        aardvark_mode: aardvarkMode
    };
    
    console.log('Executing command:', payload);
    
    // Execute command
    fetch('/api/execute_command', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        showLoading(false);
        
        console.log('Execute response:', data);
        
        if (data.success) {
            // Update hex response field
            hexResponseInput.value = data.hex_response || '';
            
            // Display dmesg logs if available (Linux only)
            updateLinuxLogsSection(data.dmesg_logs);
            
            // Display decoded output
            displayDecodedResult(data.decoded);
            
            // Save to history
            currentDecodedResult = data.decoded;
            addToHistory(selectedCommand, cmdHex, data.decoded, selectedPort);
            
            // Add to accumulated results with metadata
            allDecodedResults.push({
                command: selectedCommand,
                port: selectedPort,
                timestamp: new Date().toLocaleString(),
                decoded: data.decoded
            });
            
            // Track test result - check if there's an error in decoded data
            // Check both error key and ErrorIndicator field (bit 30 of CCI)
            const hasError = (data.decoded && data.decoded.error) || 
                           (data.decoded && data.decoded.ErrorIndicator && data.decoded.ErrorIndicator !== 0);
            let status = hasError ? 'failed' : 'passed';
            
            // Check if command is optional and failed
            if (hasError) {
                const optionalCheck = isCommandOptional(selectedCommand);
                if (optionalCheck.isOptional) {
                    status = 'n/a';
                    // Add optional note to decoded result
                    data.decoded.optional_info = optionalCheck.note;
                    data.decoded.status_override = 'Not Implemented - ' + optionalCheck.note;
                }
            }
            
            // Update command item visual indicator
            const commandItem = document.querySelector(`.command-item[data-cmd-key="${selectedCommand}"]`);
            if (commandItem) {
                commandItem.classList.remove('cmd-passed', 'cmd-failed', 'cmd-na');
                if (status === 'passed') {
                    commandItem.classList.add('cmd-passed');
                } else if (status === 'n/a') {
                    commandItem.classList.add('cmd-na');
                } else {
                    commandItem.classList.add('cmd-failed');
                }
            }
            
            // Update test results for the port
            if (!portResults[selectedPort]) {
                portResults[selectedPort] = { passed: 0, failed: 0, notRun: 0, total: 0, details: [] };
            }
            
            if (status === 'passed') {
                portResults[selectedPort].passed++;
                testResults.passed++;
            } else if (status === 'n/a') {
                portResults[selectedPort].notRun++;
                testResults.notRun++;
            } else {
                portResults[selectedPort].failed++;
                testResults.failed++;
            }
            
            portResults[selectedPort].total++;
            testResults.total++;
            
            portResults[selectedPort].details.push({
                command: selectedCommand,
                port: selectedPort,
                status: status,
                message: hasError ? data.decoded.error : 'Success'
            });
            
            testResults.details.push({
                command: selectedCommand,
                port: selectedPort,
                status: status,
                message: hasError ? data.decoded.error : 'Success'
            });
            
            // Update pie chart
            updateResultsChart();
            
            // If this is GET_CAPABILITY, extract and enable ports
            if (selectedCommand.includes('GET_CAPABILITY')) {
                extractAndEnablePorts(data.decoded, data.hex_response);
            }
            
            // Show save/copy buttons and update text
            updateSaveButtonText();
            const saveResultBtnGroup = document.getElementById('saveResultBtnGroup');
            if (saveResultBtnGroup) saveResultBtnGroup.style.display = 'inline-flex';
            if (copyResultBtn) copyResultBtn.style.display = 'inline-block';
            
            showNotification('Command executed successfully!', 'success');
        } else {
            console.log('🔍 Checking for No UCSI device error...');
            console.log('data.output:', data.output);
            console.log('Contains "No UCSI device found"?', data.output && data.output.includes('No UCSI device found'));
            
            // Display dmesg logs if available (Linux only) even on error
            updateLinuxLogsSection(data.dmesg_logs);
            
            // Check if it's a "No UCSI device found" error
            if (data.output && data.output.includes('No UCSI device found')) {
                console.log('✓ Updating device status banner for No UCSI device error');
                // Update device status banner at the top
                const statusDiv = document.getElementById('deviceStatus');
                console.log('statusDiv element:', statusDiv);
                if (statusDiv) {
                    statusDiv.innerHTML = '<span class="status-icon">❌</span><span class="status-text"><strong style="color: #dc3545;">No UCSI device found</strong></span>';
                    statusDiv.style.background = '#f8d7da';
                    statusDiv.style.borderColor = '#dc3545';
                    console.log('✓ Device status banner updated');
                } else {
                    console.error('❌ deviceStatus element not found');
                }
            }
            
            // Check if this is an optional command
            const optionalCheck = isCommandOptional(selectedCommand);
            const isOptionalCmd = optionalCheck.isOptional;
            
            if (isOptionalCmd) {
                // Show as N/A instead of error for optional commands
                outputArea.innerHTML = `
                    <div style="padding: 20px; background: #e8f4f8; border-left: 4px solid #0066cc;">
                        <h3 style="color: #004080; margin-top: 0;">ℹ️ Command Not Available</h3>
                        <p><strong>Status:</strong> N/A - Optional Command</p>
                        <p><strong>Info:</strong> ${optionalCheck.note}</p>
                        <p style="margin-top: 10px; padding: 10px; background: #fff; border-radius: 4px;">
                            <strong>Note:</strong> This command is optional and may not be implemented by this device.
                        </p>
                    </div>
                `;
            } else {
                // Show as error for required commands
                outputArea.innerHTML = `
                    <div style="padding: 20px; background: #fff3cd; border-left: 4px solid #ffc107;">
                        <h3 style="color: #856404; margin-top: 0;">⚠️ Command Execution Failed</h3>
                        <p><strong>Error:</strong> ${data.error || 'Unknown error'}</p>
                        ${data.output ? `<pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; overflow-x: auto;">${data.output}</pre>` : ''}
                    </div>
                `;
            }
            showNotification('Command execution failed: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        showLoading(false);
        console.error('Execute error:', error);
        outputArea.innerHTML = `
            <div style="padding: 20px; background: #f8d7da; border-left: 4px solid #dc3545;">
                <h3 style="color: #721c24; margin-top: 0;">❌ Error</h3>
                <p><strong>Failed to execute command:</strong> ${error.message}</p>
            </div>
        `;
        showNotification('Error: ' + error.message, 'error');
    });
}

function showCommandInstruction() {
    const cmdHex = commandHexInput.value;
    outputArea.innerHTML = `
<div style="padding: 20px; background: #f8f9fa; border-left: 4px solid #3498db; margin-bottom: 15px;">
    <h3 style="color: #2c3e50; margin-top: 0;">📌 Command Ready to Execute</h3>
    <p><strong>Command:</strong> ${selectedCommand}</p>
    <p><strong>Port:</strong> ${selectedPort}</p>
    <p><strong>Format:</strong> <code style="background: #e8f4f8; padding: 4px 8px; border-radius: 4px;">UcsiControl.exe send 0 ${cmdHex}</code></p>
    <hr style="border: none; border-top: 1px solid #ddd; margin: 15px 0;">
    <p><strong>Instructions:</strong></p>
    <ol style="margin: 10px 0; padding-left: 20px;">
        <li>Open a command prompt or terminal</li>
        <li>Run the command above using UcsiControl.exe</li>
        <li>Copy the hex response from the output</li>
        <li>Paste it in the "Hex Response Data" field above</li>
        <li>Click "Decode" to see the results</li>
    </ol>
</div>`;
}

function showConnectorResetDialog() {
    dialogTitle.textContent = 'CONNECTOR_RESET - Select Reset Type';
    dialogContent.innerHTML = `
        <div class="dialog-option" onclick="selectDialogOption('reset', 'hard')">
            <input type="radio" name="resetType" value="hard" id="reset_hard" checked>
            <label for="reset_hard">Hard Reset - Full disconnect/reconnect sequence</label>
            <div class="dialog-option-desc">Connector goes through complete disconnect-connect cycle</div>
        </div>
        <div class="dialog-option" onclick="selectDialogOption('reset', 'data')">
            <input type="radio" name="resetType" value="data" id="reset_data">
            <label for="reset_data">Data Reset - Reset USB data, preserve power</label>
            <div class="dialog-option-desc">Resets USB data and exits Alternate Modes while preserving VBUS power (requires USB4 support)</div>
        </div>
    `;
    
    dialogOverlay.style.display = 'flex';
    dialogOverlay.dataset.type = 'connector_reset';
}

function showAckCcCiDialog() {
    dialogTitle.textContent = 'ACK_CC_CI - Acknowledge Command Complete Indicator';
    dialogContent.innerHTML = `
        <div class="dialog-option" onclick="selectDialogOption('ack', 'command')">
            <input type="radio" name="ackType" value="command" id="ack_command" checked>
            <label for="ack_command">Command Completion Only</label>
            <div class="dialog-option-desc">Acknowledge command completed</div>
        </div>
        <div class="dialog-option" onclick="selectDialogOption('ack', 'connector')">
            <input type="radio" name="ackType" value="connector" id="ack_connector">
            <label for="ack_connector">Connector Change Only</label>
            <div class="dialog-option-desc">Acknowledge connector state changed</div>
        </div>
        <div class="dialog-option" onclick="selectDialogOption('ack', 'both')">
            <input type="radio" name="ackType" value="both" id="ack_both">
            <label for="ack_both">Both - Acknowledge both</label>
            <div class="dialog-option-desc">Acknowledge both command and connector change</div>
        </div>
    `;
    
    dialogOverlay.style.display = 'flex';
    dialogOverlay.dataset.type = 'ack_cc_ci';
}

function showRetimerModeDialog() {
    dialogTitle.textContent = 'SET_RETIMER_MODE - Select Retimer Mode';
    dialogContent.innerHTML = `
        <div class="dialog-option" onclick="selectDialogOption('retimer', 'usb')">
            <input type="radio" name="retimerMode" value="usb" id="retimer_usb" checked>
            <label for="retimer_usb">USB Mode - Standard USB data transfer</label>
            <div class="dialog-option-desc">Standard USB operation</div>
        </div>
        <div class="dialog-option" onclick="selectDialogOption('retimer', 'dp')">
            <input type="radio" name="retimerMode" value="dp" id="retimer_dp">
            <label for="retimer_dp">DisplayPort (DP) Mode</label>
            <div class="dialog-option-desc">Video output over USB-C</div>
        </div>
        <div class="dialog-option" onclick="selectDialogOption('retimer', 'tbt')">
            <input type="radio" name="retimerMode" value="tbt" id="retimer_tbt">
            <label for="retimer_tbt">Thunderbolt (TBT) Mode</label>
            <div class="dialog-option-desc">High-speed data and display</div>
        </div>
        <div class="dialog-option" onclick="selectDialogOption('retimer', 'usb4')">
            <input type="radio" name="retimerMode" value="usb4" id="retimer_usb4">
            <label for="retimer_usb4">USB4 Mode</label>
            <div class="dialog-option-desc">Latest USB4 protocol</div>
        </div>
    `;
    
    dialogOverlay.style.display = 'flex';
    dialogOverlay.dataset.type = 'retimer_mode';
}

function showNotificationDialog() {
    dialogTitle.textContent = 'SET_NOTIFICATION_ENABLE - Configure Notifications';
    dialogContent.innerHTML = `
        <div class="dialog-option" onclick="selectDialogOption('notif', 'none')">
            <input type="radio" name="notifLevel" value="none" id="notif_none">
            <label for="notif_none">None - Disable all notifications</label>
            <div class="dialog-option-desc">No notification events will be generated</div>
        </div>
        <div class="dialog-option" onclick="selectDialogOption('notif', 'command')">
            <input type="radio" name="notifLevel" value="command" id="notif_command" checked>
            <label for="notif_command">Command Complete Only - Default</label>
            <div class="dialog-option-desc">Notify only when commands complete</div>
        </div>
        <div class="dialog-option" onclick="selectDialogOption('notif', 'all')">
            <input type="radio" name="notifLevel" value="all" id="notif_all">
            <label for="notif_all">All Notifications - Maximum detail</label>
            <div class="dialog-option-desc">Enable all notification types (command complete, connector change, etc.)</div>
        </div>
    `;
    
    dialogOverlay.style.display = 'flex';
    dialogOverlay.dataset.type = 'notification';
}

function showPowerLevelDialog(powerType) {
    dialogTitle.textContent = `SET_POWER_LEVEL - Configure ${powerType.charAt(0).toUpperCase() + powerType.slice(1)} Power`;
    dialogContent.innerHTML = `
        <div class="dialog-input-group">
            <label for="powerLevel">Power Level (Watts):</label>
            <input type="number" id="powerLevel" min="0.5" max="240" step="0.5" value="15" placeholder="Enter power in watts">
            <div style="margin-top: 8px; font-size: 13px; color: #666;">
                Common values: 5W, 9W, 15W, 20W, 27W, 45W, 60W, 100W
            </div>
        </div>
    `;
    
    dialogOverlay.style.display = 'flex';
    dialogOverlay.dataset.type = 'power_level';
    dialogOverlay.dataset.powerType = powerType;
}

function showReadPowerLevelDialog() {
    dialogTitle.textContent = 'READ_POWER_LEVEL - Configure Reading Parameters';
    dialogContent.innerHTML = `
        <div class="dialog-input-group">
            <label for="timeToRead">Time to Read (0-255):</label>
            <input type="number" id="timeToRead" min="0" max="255" value="0" placeholder="0">
            <div style="margin-top: 4px; font-size: 13px; color: #666;">
                Actual time = (value × 100) + 100 ms. 0 = 100ms, 1 = 200ms, etc.
            </div>
        </div>
        <div class="dialog-input-group">
            <label for="timeInterval">Time Interval (0-255):</label>
            <input type="number" id="timeInterval" min="0" max="255" value="1" placeholder="1">
            <div style="margin-top: 4px; font-size: 13px; color: #666;">
                Actual interval = (value × 5) + 5 ms. 0 = 5ms, 1 = 10ms, etc.
            </div>
        </div>
    `;
    
    dialogOverlay.style.display = 'flex';
    dialogOverlay.dataset.type = 'read_power_level';
}

function showUorDialog() {
    dialogTitle.textContent = 'SET_UOR - USB Operation Role';
    dialogContent.innerHTML = `
        <div class="dialog-option" onclick="selectDialogOption('uor', 'dfp')">
            <input type="radio" name="uorMode" value="dfp" id="uor_dfp" checked>
            <label for="uor_dfp">DFP - Downstream Facing Port (Host)</label>
            <div class="dialog-option-desc">Acts as USB host</div>
        </div>
        <div class="dialog-option" onclick="selectDialogOption('uor', 'ufp')">
            <input type="radio" name="uorMode" value="ufp" id="uor_ufp">
            <label for="uor_ufp">UFP - Upstream Facing Port (Device)</label>
            <div class="dialog-option-desc">Acts as USB device</div>
        </div>
        <div class="dialog-option" onclick="selectDialogOption('uor', 'swap')">
            <input type="radio" name="uorMode" value="swap" id="uor_swap">
            <label for="uor_swap">Accept Swap - Allow role swap</label>
            <div class="dialog-option-desc">Accept USB data role swap requests</div>
        </div>
    `;
    
    dialogOverlay.style.display = 'flex';
    dialogOverlay.dataset.type = 'uor';
}

function showPdrDialog() {
    dialogTitle.textContent = 'SET_PDR - Power Direction Role';
    dialogContent.innerHTML = `
        <div class="dialog-option" onclick="selectDialogOption('pdr', 'provider')">
            <input type="radio" name="pdrMode" value="provider" id="pdr_provider" checked>
            <label for="pdr_provider">Provider - Supply power</label>
            <div class="dialog-option-desc">This port provides power (source)</div>
        </div>
        <div class="dialog-option" onclick="selectDialogOption('pdr', 'consumer')">
            <input type="radio" name="pdrMode" value="consumer" id="pdr_consumer">
            <label for="pdr_consumer">Consumer - Receive power</label>
            <div class="dialog-option-desc">This port consumes power (sink)</div>
        </div>
        <div class="dialog-option" onclick="selectDialogOption('pdr', 'swap')">
            <input type="radio" name="pdrMode" value="swap" id="pdr_swap">
            <label for="pdr_swap">Accept Swap - Allow power role swap</label>
            <div class="dialog-option-desc">Accept power role swap requests</div>
        </div>
    `;
    
    dialogOverlay.style.display = 'flex';
    dialogOverlay.dataset.type = 'pdr';
}

function showAlternateModesDialog() {
    dialogTitle.textContent = 'GET_ALTERNATE_MODES - Select Recipient';
    dialogContent.innerHTML = `
        <div class="dialog-option" onclick="selectDialogOption('altmode', 'connector')">
            <input type="radio" name="altmodeRecipient" value="connector" id="altmode_connector" checked>
            <label for="altmode_connector">Connector - Query this port</label>
            <div class="dialog-option-desc">Get alternate modes supported by this connector</div>
        </div>
        <div class="dialog-option" onclick="selectDialogOption('altmode', 'partner')">
            <input type="radio" name="altmodeRecipient" value="partner" id="altmode_partner">
            <label for="altmode_partner">Partner - Query connected device</label>
            <div class="dialog-option-desc">Get alternate modes supported by the connected device</div>
        </div>
    `;
    
    dialogOverlay.style.display = 'flex';
    dialogOverlay.dataset.type = 'alternate_modes';
}

function showSetUsbDialog() {
    dialogTitle.textContent = 'SET_USB - Configure USB Mode';
    dialogContent.innerHTML = `
        <div class="dialog-option" onclick="selectDialogOption('setusb', 'enable_usb4')">
            <input type="radio" name="usbMode" value="enable_usb4" id="usb_enable4" checked>
            <label for="usb_enable4">Enable USB4</label>
            <div class="dialog-option-desc">Enable USB4 operation</div>
        </div>
        <div class="dialog-option" onclick="selectDialogOption('setusb', 'disable_usb4')">
            <input type="radio" name="usbMode" value="disable_usb4" id="usb_disable4">
            <label for="usb_disable4">Disable USB4</label>
            <div class="dialog-option-desc">Disable USB4 operation</div>
        </div>
        <div class="dialog-option" onclick="selectDialogOption('setusb', 'enable_usb3')">
            <input type="radio" name="usbMode" value="enable_usb3" id="usb_enable3">
            <label for="usb_enable3">Enable USB3</label>
            <div class="dialog-option-desc">Enable USB3 operation</div>
        </div>
        <div class="dialog-option" onclick="selectDialogOption('setusb', 'disable_usb3')">
            <input type="radio" name="usbMode" value="disable_usb3" id="usb_disable3">
            <label for="usb_disable3">Disable USB3 operation</label>
            <div class="dialog-option-desc">Disable USB3 operation</div>
        </div>
    `;
    
    dialogOverlay.style.display = 'flex';
    dialogOverlay.dataset.type = 'set_usb';
}

function showSetNewCamDialog() {
    dialogTitle.textContent = 'SET_NEW_CAM - Configure Alternate Mode';
    
    // Show loading state while fetching alternate modes
    dialogContent.innerHTML = `
        <div style="text-align: center; padding: 40px;">
            <div style="font-size: 16px; margin-bottom: 20px;">Loading alternate modes...</div>
            <div style="font-size: 14px; color: #666;">
                Querying GET_ALTERNATE_MODES and GET_CAM_SUPPORTED for Port ${selectedPort}...
            </div>
        </div>
    `;
    
    dialogOverlay.style.display = 'flex';
    dialogOverlay.dataset.type = 'set_new_cam';
    
    // Hide the OK/Cancel buttons during loading
    const dialogButtons = document.querySelector('.dialog-buttons');
    if (dialogButtons) {
        dialogButtons.style.display = 'none';
    }
    
    // Automatically fetch alternate modes before showing the form
    fetchAlternateModesForSetNewCam();
}

// Add a flag to prevent concurrent fetches
let isFetchingAlternateModes = false;

async function fetchAlternateModesForSetNewCam() {
    // Prevent concurrent fetches - if already fetching, skip this call
    if (isFetchingAlternateModes) {
        console.warn('[Background] Already fetching alternate modes, skipping duplicate request');
        return;
    }
    
    isFetchingAlternateModes = true;
    
    try {
        const connectorNum = selectedPort;
        
        console.log('[Background] Fetching alternate modes for port', connectorNum, 'Aardvark mode:', aardvarkMode);
        
        // Step 1: Get alternate modes (Connector)
        // For Aardvark mode, use command name and let backend build the command
        // For Normal mode, build the command hex based on platform
        
        let altModesCmd;
        let altModesCmdKey;
        
        if (aardvarkMode) {
            // Aardvark mode: Use command name, backend will build the hex
            altModesCmdKey = 'C - GET_ALTERNATE_MODES (Connector)';
            altModesCmd = '00';  // Placeholder - backend ignores this and uses command name
            console.log('[Background] Using Aardvark command:', altModesCmdKey);
        } else if (platformInfo.is_windows) {
            // Windows format: 16 hex chars as <HighDW><LowDW>
            // GET_ALTERNATE_MODES: LowDW has connector in bits 24-31 and command 0x0C in bits 0-7
            //                     HighDW has num_modes=1 in bits 8-15 (byte 5)
            const connectorHex = connectorNum.toString(16).padStart(2, '0');
            altModesCmd = `00000100${connectorHex}00000C`;
            altModesCmdKey = 'C - GET_ALTERNATE_MODES';
            console.log('[Background] Using Windows command:', altModesCmd);
        } else {
            // Linux format: Build as 64-bit value, convert to minimal hex
            const byte0 = 0x0C;
            const byte1 = 0x00;
            const byte2 = 0x00;  // Connector recipient
            const byte3 = connectorNum;
            const byte4 = 0x00;
            const byte5 = 0x01;
            const byte6 = 0x00;
            const byte7 = 0x00;
            
            const cmd64bit = 
                (BigInt(byte7) << BigInt(56)) |
                (BigInt(byte6) << BigInt(48)) |
                (BigInt(byte5) << BigInt(40)) |
                (BigInt(byte4) << BigInt(32)) |
                (BigInt(byte3) << BigInt(24)) |
                (BigInt(byte2) << BigInt(16)) |
                (BigInt(byte1) << BigInt(8)) |
                BigInt(byte0);
            
            altModesCmd = cmd64bit.toString(16).toUpperCase();
            altModesCmdKey = 'C - GET_ALTERNATE_MODES';
            console.log('[Background] Using Linux command:', altModesCmd);
        }
        
        // Log the exact payload being sent
        const altModesPayload = {
            command_key: altModesCmdKey,
            command_hex: altModesCmd,
            port: connectorNum,
            ucsi_version: detectedVersion,
            aardvark_mode: aardvarkMode
        };
        console.log('[Background] Sending GET_ALTERNATE_MODES payload:', JSON.stringify(altModesPayload));
        
        const altModesResponse = await fetch('/api/execute_command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(altModesPayload)
        });
        
        console.log('[Background] GET_ALTERNATE_MODES HTTP status:', altModesResponse.status, altModesResponse.statusText);
        
        const altModesData = await altModesResponse.json();
        console.log('[Background] GET_ALTERNATE_MODES response:', altModesData);
        console.log('[Background] Response keys:', Object.keys(altModesData));
        console.log('[Background] altModesData.success:', altModesData.success);
        console.log('[Background] altModesData.decoded:', altModesData.decoded);
        if (altModesData.decoded) {
            console.log('[Background] decoded keys:', Object.keys(altModesData.decoded));
            console.log('[Background] decoded.alternate_modes:', altModesData.decoded.alternate_modes);
        }
        
        // Check for errors
        if (!altModesResponse.ok || altModesData.error) {
            console.error('[Background] GET_ALTERNATE_MODES failed with status', altModesResponse.status);
            console.error('[Background] Error details:', altModesData.error || altModesData);
            detectedAlternateModes = [];
        } else if (altModesData.success && altModesData.decoded && altModesData.decoded.alternate_modes) {
            detectedAlternateModes = altModesData.decoded.alternate_modes;
            console.log('[Background] Fetched alternate modes:', detectedAlternateModes);
        } else if (altModesData.success && altModesData.decoded && altModesData.decoded.message) {
            // Empty response case (e.g., Port 2 with no modes)
            console.log('[Background] No alternate modes available:', altModesData.decoded.message);
            detectedAlternateModes = [];
        } else {
            console.warn('[Background] Unexpected response structure:', altModesData);
            detectedAlternateModes = [];
        }
        
        // Note: GET_CAM_SUPPORTED is NOT used for SET_NEW_CAM dialog
        // According to UCSI spec, GET_CAM_SUPPORTED returns a bitmap indicating which modes
        // are currently available (may be subset if resources used by other connectors).
        // For SET_NEW_CAM, we show ALL detected alternate modes from GET_ALTERNATE_MODES.
        // The user can attempt to enter any mode; the PPM will reject if not supported.
        console.log('[Background] Skipping GET_CAM_SUPPORTED - using all detected modes for SET_NEW_CAM');
        
        // Now show the actual dialog with populated data
        showSetNewCamDialogForm();
        
    } catch (error) {
        console.error('[Background] Error fetching alternate modes:', error);
        detectedAlternateModes = [];
        showSetNewCamDialogForm();
    } finally {
        // Always release the mutex
        isFetchingAlternateModes = false;
        console.log('[Background] Fetch complete, mutex released');
    }
}

function showSetNewCamDialogForm() {
    console.log('=== SET_NEW_CAM Dialog Debug ===');
    console.log('detectedAlternateModes:', detectedAlternateModes);
    console.log('Number of modes:', detectedAlternateModes ? detectedAlternateModes.length : 0);
    
    // Build alternate mode options with actual mode names
    let modeOptions = '<option value="0xFF">Exit All Modes (0xFF)</option>';
    let workflowWarning = '';
    
    if (detectedAlternateModes && detectedAlternateModes.length > 0) {
        // Use detected alternate modes with their names
        console.log('Building SET_NEW_CAM dialog with modes:', detectedAlternateModes);
        detectedAlternateModes.forEach((mode) => {
            console.log('Processing mode:', mode);
            const modeName = mode.name || `Mode ${mode.index}`;
            const modeIndex = mode.index !== undefined ? mode.index : 0;
            const optionText = `Offset ${modeIndex}: ${modeName} (SVID: ${mode.svid})`;
            console.log('Adding option:', optionText, 'with value:', modeIndex);
            modeOptions += `<option value="${modeIndex}">${optionText}</option>`;
        });
        console.log('Final modeOptions HTML:', modeOptions);
    } else {
        // Show warning if no modes have been detected
        workflowWarning = `
            <div class="workflow-warning">
                <strong>⚠️ No Alternate Modes Detected</strong><br>
                The connector does not report any alternate modes, or they could not be retrieved.<br>
                You can still use Exit All Modes, or manually specify an offset.
            </div>
        `;
        // Fallback to generic offsets if no modes detected
        modeOptions += '<option value="0">Offset 0 (Unknown Mode)</option>';
        modeOptions += '<option value="1">Offset 1 (Unknown Mode)</option>';
        modeOptions += '<option value="2">Offset 2 (Unknown Mode)</option>';
        modeOptions += '<option value="3">Offset 3 (Unknown Mode)</option>';
    }
    
    dialogContent.innerHTML = `
        <style>
            .newcam-section { margin-bottom: 20px; }
            .newcam-section-title { font-weight: 600; margin-bottom: 10px; color: #2c3e50; }
            .newcam-row { display: flex; gap: 15px; margin-bottom: 15px; align-items: center; }
            .newcam-field { flex: 1; }
            .newcam-field label { display: block; margin-bottom: 5px; font-weight: 500; color: #555; }
            .newcam-field select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }
            .newcam-field input[type="text"] { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }
            .dp-config-section { margin-top: 15px; padding: 15px; background: #f8f9fa; border-radius: 6px; border: 1px solid #e0e0e0; }
            .dp-config-options { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px; }
            .dp-config-option { padding: 8px; background: white; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; font-size: 13px; }
            .dp-config-option:hover { background: #e8f4f8; border-color: #0066cc; }
            .dp-config-option input[type="radio"] { margin-right: 6px; }
            .info-text { font-size: 12px; color: #666; margin-top: 5px; font-style: italic; }
            .warning-text { font-size: 12px; color: #f39c12; margin-top: 5px; font-style: italic; }
            .workflow-warning { 
                background: #fff3cd; 
                border: 1px solid #ffc107; 
                padding: 12px; 
                border-radius: 6px; 
                margin-bottom: 20px; 
                font-size: 13px; 
                line-height: 1.6;
                color: #856404;
            }
        </style>
        
        ${workflowWarning}
        
        <div class="newcam-section">
            <div class="newcam-section-title">Connector Port ${selectedPort} - Configure Action</div>
            <div class="newcam-field">
                <label for="newcam_action">Action</label>
                <select id="newcam_action" onchange="updateNewCamPreview()">
                    <option value="exit">Exit Alternate Mode</option>
                    <option value="enter">Enter Alternate Mode</option>
                </select>
            </div>
        </div>

        <div class="newcam-section">
            <div class="newcam-section-title">Alternate Mode</div>
            <div class="newcam-field">
                <label for="newcam_mode">Select Alternate Mode</label>
                <select id="newcam_mode" onchange="updateNewCamPreview()">
                    ${modeOptions}
                </select>
                <div class="info-text">
                    Offset refers to the position in GET_ALTERNATE_MODES list. 
                    Use GET_CAM_SUPPORTED to verify which modes are currently available.
                </div>
            </div>
        </div>

        <div id="dp_config_section" class="dp-config-section" style="display: none;">
            <div class="newcam-section-title">DisplayPort Configuration (AMSpecific)</div>
            <div class="dp-config-options">
                <div class="dp-config-option" onclick="selectDPConfig('0x00000000')">
                    <input type="radio" name="dpConfig" value="0x00000000" id="dp_default" checked>
                    <label for="dp_default">Default (0x00000000)</label>
                </div>
                <div class="dp-config-option" onclick="selectDPConfig('0x00000001')">
                    <input type="radio" name="dpConfig" value="0x00000001" id="dp_c">
                    <label for="dp_c">Config C (0x00000001)</label>
                </div>
                <div class="dp-config-option" onclick="selectDPConfig('0x00000002')">
                    <input type="radio" name="dpConfig" value="0x00000002" id="dp_d">
                    <label for="dp_d">Config D (0x00000002)</label>
                </div>
                <div class="dp-config-option" onclick="selectDPConfig('0x00000003')">
                    <input type="radio" name="dpConfig" value="0x00000003" id="dp_e">
                    <label for="dp_e">Config E (0x00000003)</label>
                </div>
            </div>
            <div class="newcam-field" style="margin-top: 10px;">
                <label for="newcam_amspecific">Custom AMSpecific (Hex, 8 digits)</label>
                <input type="text" id="newcam_amspecific" value="00000000" maxlength="8" oninput="validateHexInput(this)" onchange="updateNewCamPreview()" placeholder="00000000">
                <div class="info-text">32-bit value for AM-specific configuration</div>
            </div>
        </div>

        <div class="newcam-section" style="margin-top: 20px; padding-top: 15px; border-top: 2px solid #e0e0e0;">
            <div class="newcam-section-title">Command Preview</div>
            <div class="newcam-field">
                <input type="text" id="newcam_preview" readonly style="font-family: monospace; background: #f0f0f0; font-weight: 600; color: #0066cc;">
            </div>
        </div>
    `;
    
    dialogOverlay.dataset.type = 'set_new_cam';
    
    // Show the OK/Cancel buttons now that form is ready
    const dialogButtons = document.querySelector('.dialog-buttons');
    if (dialogButtons) {
        dialogButtons.style.display = 'flex';
    }
    
    // Initialize preview
    setTimeout(() => updateNewCamPreview(), 100);
}

function selectDPConfig(value) {
    document.querySelectorAll('input[name="dpConfig"]').forEach(r => {
        r.checked = r.value === value;
    });
    document.getElementById('newcam_amspecific').value = value.substring(2); // Remove 0x
    updateNewCamPreview();
}

function updateNewCamPreview() {
    const port = selectedPort.toString(); // Use globally selected port
    const action = document.getElementById('newcam_action')?.value || 'exit';
    const mode = document.getElementById('newcam_mode')?.value || '0xFF';
    const amspecific = document.getElementById('newcam_amspecific')?.value || '00000000';
    
    // Check if selected mode is DisplayPort (SVID 0xFF01)
    let isDisplayPort = false;
    if (mode !== '0xFF' && detectedAlternateModes && detectedAlternateModes.length > 0) {
        const modeIndex = parseInt(mode);
        if (modeIndex >= 0 && modeIndex < detectedAlternateModes.length) {
            const selectedMode = detectedAlternateModes[modeIndex];
            isDisplayPort = selectedMode.svid === '0xFF01' || selectedMode.name === 'DisplayPort';
        }
    }
    
    // Show/hide DP config section
    const dpSection = document.getElementById('dp_config_section');
    if (dpSection) {
        dpSection.style.display = (isDisplayPort && action === 'enter') ? 'block' : 'none';
    }
    
    // Build command hex
    // Format: [AMSpecific 32bit][New CAM 8bit][Connector+Enter/Exit 8bit][DataLen 8bit][Command 8bit]
    const cmd = '0F'; // SET_NEW_CAM
    const dataLen = '00';
    
    // Connector number (7 bits) + EnterOrExit bit (1 bit)
    const connectorNum = parseInt(port);
    const enterBit = action === 'enter' ? 0x80 : 0x00;
    const connectorByte = (connectorNum | enterBit).toString(16).padStart(2, '0').toUpperCase();
    
    // New CAM offset
    let camOffset = mode === '0xFF' ? 'FF' : parseInt(mode).toString(16).padStart(2, '0').toUpperCase();
    
    // AMSpecific (only used for enter mode and non-exit-all)
    let amSpecificHex = '00000000';
    if (action === 'enter' && mode !== '0xFF') {
        amSpecificHex = amspecific.padStart(8, '0').toUpperCase();
    }
    
    // Build final hex: AMSpecific + NewCAM + Connector + DataLen + Command
    const fullHex = amSpecificHex + camOffset + connectorByte + dataLen + cmd;
    
    // Update preview
    const preview = document.getElementById('newcam_preview');
    if (preview) {
        preview.value = fullHex;
    }
}

function validateHexInput(input) {
    // Remove any non-hex characters
    input.value = input.value.replace(/[^0-9A-Fa-f]/g, '').toUpperCase();
}

function convertWindowsHexToLinux(windowsHex) {
    /**
     * Convert Windows UCSI command format to Linux minimal hex format.
     * Windows format: 16 hex chars representing 2 DWORDs (LowDW + HighDW)
     * Linux format: minimal hex representation of 64-bit little-endian value
     * 
     * Example: '000001000100000C' (Windows) -> '1000100000C' (Linux)
     */
    if (!windowsHex || windowsHex.length !== 16) {
        // If not 16 chars, assume it's already in correct format or invalid
        return windowsHex;
    }
    
    // Parse as two DWORDs: first 8 chars = HighDW, last 8 chars = LowDW
    const highDWHex = windowsHex.substring(0, 8);
    const lowDWHex = windowsHex.substring(8, 16);
    
    // Convert to integers
    const lowDW = parseInt(lowDWHex, 16);
    const highDW = parseInt(highDWHex, 16);
    
    // Build 64-bit value: HighDW in upper 32 bits, LowDW in lower 32 bits
    const cmd64bit = (BigInt(highDW) << BigInt(32)) | BigInt(lowDW);
    
    // Convert to minimal hex (no leading zeros)
    return cmd64bit.toString(16).toUpperCase();
}

function selectDialogOption(group, value) {
    const radios = document.querySelectorAll(`input[name="${group}Mode"], input[name="${group}Level"], input[name="${group}Recipient"]`);
    radios.forEach(r => {
        r.checked = r.value === value;
    });
}

function handleDialogOk() {
    const dialogType = dialogOverlay.dataset.type;
    
    if (dialogType === 'notification') {
        const selected = document.querySelector('input[name="notifLevel"]:checked')?.value || 'command';
        const configs = {
            'none': '0000000000000005',        // No notifications
            'command': '0000000000010005',     // Command Complete only (bit 0)
            'all': '00000000ffff0005'          // All notifications enabled
        };
        const cmdHex = configs[selected];
        const descriptions = {
            'none': 'None',
            'command': 'Command Complete Only',
            'all': 'All Notifications'
        };
        
        // Set the selectedCommand to ensure proper command_key is sent to server
        const aardvarkCmdName = selected === 'all' ? '5 - SET_NOTIFICATION_ENABLE (all)' : '5 - SET_NOTIFICATION_ENABLE (none)';
        selectedCommand = aardvarkMode ? aardvarkCmdName : '5 - SET_NOTIFICATION_ENABLE';
        selectedCommandInput.value = selectedCommand;
        
        // Update command hex input
        const finalHex = platformInfo.is_linux ? convertWindowsHexToLinux(cmdHex) : cmdHex;
        commandHexInput.value = platformInfo.is_windows ? `UcsiControl.exe send 0 ${cmdHex}` : `echo 0x${finalHex} > command`;
        commandHexInput.dataset.rawHex = finalHex;
        
        // Close dialog first
        closeDialog();
        
        // Execute the command
        executeCommand();
        return; // Skip the closeDialog at the end since we already called it
        
    } else if (dialogType === 'power_level') {
        const powerLevel = parseFloat(document.getElementById('powerLevel')?.value || 15);
        const powerType = dialogOverlay.dataset.powerType;
        const typeFlag = powerType === 'source' ? '81' : '01';
        
        // Build command hex: 0x14 (command) + 0x03 (data length) + type flag + power level bytes
        // Power level is in 0.5W units (e.g., 15W = 30 * 0.5W = 0x1E)
        const powerUnits = Math.round(powerLevel * 2); // Convert watts to 0.5W units
        const powerByte = powerUnits.toString(16).padStart(2, '0').toUpperCase();
        
        // Command format: [reserved] [power] [flags] [data_len] [cmd]
        // Windows format (reversed): 00 [power] [flags] 03 00 14
        const cmdHex = `00${powerByte}${typeFlag}030014`;
        
        // Set the selectedCommand to ensure proper command_key is sent to server
        selectedCommand = '14 - SET_POWER_LEVEL';
        selectedCommandInput.value = selectedCommand;
        
        // Update command hex input
        const finalHex = platformInfo.is_linux ? convertWindowsHexToLinux(cmdHex) : cmdHex;
        commandHexInput.value = platformInfo.is_windows ? `UcsiControl.exe send 0 ${cmdHex}` : `echo 0x${finalHex} > command`;
        commandHexInput.dataset.rawHex = cmdHex;
        
        // Close dialog first
        closeDialog();
        
        // Execute the command
        executeCommand();
        return; // Skip the closeDialog at the end since we already called it
        
    } else if (dialogType === 'read_power_level') {
        const timeToRead = parseInt(document.getElementById('timeToRead')?.value || 0);
        const timeInterval = parseInt(document.getElementById('timeInterval')?.value || 1);
        
        // Build command hex based on selected port and user inputs
        // Per UCSI Table 6-85:
        // Bits 16-22: Connector Number (7 bits)
        // Bits 23-27: Time to Read Power (5 bits) - value * 100ms
        // Bits 28-30: Reserved (3 bits) - must be 0
        // Bits 31-32: Time Interval (2 bits) - value * 5ms
        
        const port = selectedPort;
        
        // Byte 2 (bits 16-23): Connector (bits 0-6) + Time to Read bit 0 (bit 7)
        const byte2 = (port & 0x7F) | ((timeToRead & 0x01) << 7);
        
        // Byte 3 (bits 24-31): Time to Read bits 1-4 (bits 0-3) + Reserved (bits 4-6) + Time Interval bit 0 (bit 7)
        const byte3 = ((timeToRead >> 1) & 0x0F) | ((timeInterval & 0x01) << 7);
        
        // Build command: Windows format is reversed bytes
        // Little-endian: 1E 00 [byte2] [byte3]
        // Windows display: [byte3] [byte2] 00 1E
        const cmdHex = `${byte3.toString(16).padStart(2, '0').toUpperCase()}${byte2.toString(16).padStart(2, '0').toUpperCase()}001E`;
        
        // Calculate actual timing for display
        const actualTimeMs = (timeToRead + 1) * 100;
        const actualIntervalMs = (timeInterval + 1) * 5;
        
        console.log(`READ_POWER_LEVEL: Port ${port}, Time=${actualTimeMs}ms, Interval=${actualIntervalMs}ms, Command=${cmdHex}`);
        
        // Set the selectedCommand to ensure proper command_key is sent to server
        selectedCommand = '1E - READ_POWER_LEVEL';
        selectedCommandInput.value = selectedCommand;
        
        // Update command hex input
        commandHexInput.value = platformInfo.is_windows ? `UcsiControl.exe send 0 ${cmdHex}` : `echo 0x${cmdHex} > command`;
        commandHexInput.dataset.rawHex = cmdHex;
        
        // Store the READ_POWER_LEVEL command info to restore after background GET_CONNECTOR_STATUS
        const readPowerLevelCommand = selectedCommand;
        const readPowerLevelHex = cmdHex;
        const readPowerLevelDisplay = commandHexInput.value;
        
        // Close dialog first
        closeDialog();
        
        // Execute READ_POWER_LEVEL command
        executeCommand();
        
        // After command execution, check ErrorIndicator and run GET_CONNECTOR_STATUS if successful
        // Wait for command to complete and check result
        setTimeout(() => {
            // Check if last command had an error
            if (currentDecodedResult && currentDecodedResult.ErrorIndicator === 1) {
                console.log('READ_POWER_LEVEL returned ErrorIndicator=1, skipping GET_CONNECTOR_STATUS');
                return;
            }
            
            console.log('READ_POWER_LEVEL successful (ErrorIndicator=0), fetching power data via GET_CONNECTOR_STATUS in background...');
            
            // Save current UI state before background command
            const savedCommand = selectedCommand;
            const savedCommandDisplay = selectedCommandInput.value;
            const savedHexDisplay = commandHexInput.value;
            const savedRawHex = commandHexInput.dataset.rawHex;
            
            // Temporarily set GET_CONNECTOR_STATUS command (internal only)
            selectedCommand = '12 - GET_CONNECTOR_STATUS';
            
            // Build GET_CONNECTOR_STATUS hex with same port
            // Format: port (1 byte) + reserved (1 byte) + command 0x12
            const statusCmdHex = `${port.toString(16).padStart(2, '0').toUpperCase()}0012`;
            commandHexInput.dataset.rawHex = statusCmdHex;
            
            // Execute GET_CONNECTOR_STATUS silently in background
            const payload = {
                command_key: '12 - GET_CONNECTOR_STATUS',
                command_hex: statusCmdHex,
                port: port,
                ucsi_version: detectedVersion,
                aardvark_mode: aardvarkMode
            };
            
            fetch('/api/execute_command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('Background GET_CONNECTOR_STATUS completed, displaying power data...');
                    
                    // Display the connector status results
                    displayDecodedResult(data.decoded);
                    
                    // Update history with GET_CONNECTOR_STATUS
                    addToHistory('12 - GET_CONNECTOR_STATUS', statusCmdHex, data.decoded, port);
                }
                
                // Restore READ_POWER_LEVEL command in UI
                selectedCommand = readPowerLevelCommand;
                selectedCommandInput.value = readPowerLevelCommand;
                commandHexInput.value = readPowerLevelDisplay;
                commandHexInput.dataset.rawHex = readPowerLevelHex;
            })
            .catch(error => {
                console.error('Background GET_CONNECTOR_STATUS failed:', error);
                
                // Restore READ_POWER_LEVEL command in UI even on error
                selectedCommand = readPowerLevelCommand;
                selectedCommandInput.value = readPowerLevelCommand;
                commandHexInput.value = readPowerLevelDisplay;
                commandHexInput.dataset.rawHex = readPowerLevelHex;
            });
        }, 1500); // 1500ms delay to allow command completion and LPM to prepare data
        return; // Skip the closeDialog at the end since we already called it
        
    } else if (dialogType === 'uor') {
        const selected = document.querySelector('input[name="uorMode"]:checked')?.value || 'dfp';
        // UCSI CONTROL: byte3=roleBitsHigh, byte2=(roleBitLow|connector), byte1=0x00, byte0=0x09
        const roleConfigs = {
            'dfp':  { byte3: 0x00, byte2_role: 0x80 },  // bit 23 = DFP
            'ufp':  { byte3: 0x01, byte2_role: 0x00 },  // bit 24 = UFP
            'swap': { byte3: 0x02, byte2_role: 0x00 }   // bit 25 = Accept Swap
        };
        const descriptions = {
            'dfp': 'Swap to DFP',
            'ufp': 'Swap to UFP',
            'swap': 'Accept Swap'
        };
        const aardvarkCommands = {
            'dfp': '9 - SET_UOR (Swap to DFP)',
            'ufp': '9 - SET_UOR (Swap to UFP)',
            'swap': '9 - SET_UOR (Accept Swap)'
        };
        const role = roleConfigs[selected];
        const byte2 = role.byte2_role | selectedPort;
        const rawHex = role.byte3.toString(16).padStart(2, '0') +
                       byte2.toString(16).padStart(2, '0') + '0009';
        const cmdHex = rawHex.replace(/^0+/, '') || '0';
        const fullCommandName = aardvarkMode ? aardvarkCommands[selected] : `9 - SET_UOR (${descriptions[selected]})`;
        selectedCommand = fullCommandName;
        selectedCommandInput.value = fullCommandName;
        showCommandExecutionInfo(cmdHex, fullCommandName);
        
    } else if (dialogType === 'pdr') {
        const selected = document.querySelector('input[name="pdrMode"]:checked')?.value || 'provider';
        // UCSI CONTROL: byte3=roleBitsHigh, byte2=(roleBitLow|connector), byte1=0x00, byte0=0x0B
        const roleConfigs = {
            'provider': { byte3: 0x00, byte2_role: 0x80 },  // bit 23 = Provider/Source
            'consumer': { byte3: 0x01, byte2_role: 0x00 },  // bit 24 = Consumer/Sink
            'swap':     { byte3: 0x02, byte2_role: 0x00 }   // bit 25 = Accept Swap
        };
        const descriptions = {
            'provider': 'Swap to Provider',
            'consumer': 'Swap to Consumer',
            'swap': 'Accept Swap'
        };
        const aardvarkCommands = {
            'provider': 'B - SET_PDR (Swap to Provider)',
            'consumer': 'B - SET_PDR (Swap to Consumer)',
            'swap': 'B - SET_PDR (Accept Swap)'
        };
        const role = roleConfigs[selected];
        const byte2 = role.byte2_role | selectedPort;
        const rawHex = role.byte3.toString(16).padStart(2, '0') +
                       byte2.toString(16).padStart(2, '0') + '000b';
        const cmdHex = rawHex.replace(/^0+/, '') || '0';
        const fullCommandName = aardvarkMode ? aardvarkCommands[selected] : `B - SET_PDR (${descriptions[selected]})`;
        selectedCommand = fullCommandName;
        selectedCommandInput.value = fullCommandName;
        showCommandExecutionInfo(cmdHex, fullCommandName);
        
    } else if (dialogType === 'alternate_modes') {
        const selected = document.querySelector('input[name="altmodeRecipient"]:checked')?.value || 'connector';
        // GET_ALTERNATE_MODES format per UCSI Table 6-24 (8-byte command):
       
        const port = selectedPort; // Connector number
        const recipient = selected === 'partner' ? 0x80 : 0x00; // 0x00=Connector modes, 0x80=Partner/SOP modes (bit 7)
        
        // Build 8-byte command in little-endian order
        const byte0 = 0x0C; // Command
        const byte1 = 0x00; // Data Length (0x00 in command)
        const byte2 = recipient; // Recipient: bit 7 set for Partner
        const byte3 = port;  // Connector Number in bits 0-6
        const byte4 = 0x00; // Alternate Mode Offset (start from 0)
        const byte5 = 0x01; // Number of modes (1 = request 2 modes)
        const byte6 = 0x00; // Reserved
        const byte7 = 0x00; // Reserved
        
        // Build 64-bit command as two 32-bit DWORDs (little-endian)
        // LowDW = bytes 0-3, HighDW = bytes 4-7
        const lowDW = (byte3 << 24) | (byte2 << 16) | (byte1 << 8) | byte0;
        const highDW = (byte7 << 24) | (byte6 << 16) | (byte5 << 8) | byte4;
        
        // Format as hex strings (8 chars each, zero-padded)
        const lowDWHex = lowDW.toString(16).padStart(8, '0').toUpperCase();
        const highDWHex = highDW.toString(16).padStart(8, '0').toUpperCase();
        
        // For Windows: Command format is <HighDW><LowDW> (big-endian hex)
        // UcsiControl.exe send <HighDW> <LowDW>
        // For Linux: Command format is 8 bytes in little-endian order (byte0 byte1 byte2...byte7)
        // BUT: Linux kernel expects minimal hex representation (no leading zeros after combining bytes into 64-bit value)
        let cmdHex;
        if (platformInfo.is_windows) {
            cmdHex = `${highDWHex}${lowDWHex}`;
        } else {
            // Linux: Combine all 8 bytes into a 64-bit value, then convert to minimal hex (no leading zeros)
            // Build as: byte7 byte6 byte5 byte4 byte3 byte2 byte1 byte0 (big-endian for display)
            // Create the 64-bit value by combining bytes properly
            const cmd64bit = 
                (BigInt(byte7) << BigInt(56)) |
                (BigInt(byte6) << BigInt(48)) |
                (BigInt(byte5) << BigInt(40)) |
                (BigInt(byte4) << BigInt(32)) |
                (BigInt(byte3) << BigInt(24)) |
                (BigInt(byte2) << BigInt(16)) |
                (BigInt(byte1) << BigInt(8)) |
                BigInt(byte0);
            
            // Convert to hex without leading zeros (kernel expects minimal representation)
            cmdHex = cmd64bit.toString(16).toUpperCase();
        }
        
        const description = `C - GET_ALTERNATE_MODES (${selected.charAt(0).toUpperCase() + selected.slice(1)})`;
        
        // Set the selectedCommand to ensure proper command_key is sent to server
        // For Aardvark mode, use the exact command name from COMMAND_MAP
        if (aardvarkMode) {
            selectedCommand = selected === 'partner' 
                ? 'C - GET_ALTERNATE_MODES (Partner)' 
                : 'C - GET_ALTERNATE_MODES (Connector)';
        } else {
            selectedCommand = 'C - GET_ALTERNATE_MODES';
        }
        selectedCommandInput.value = selectedCommand;
        
        // Update command hex input based on mode
        if (aardvarkMode) {
            // Aardvark mode: Build I2C command with 09 08 header
            // Format: DATA_REG (09) + NUM_BYTES (08) + 8 UCSI command bytes
            const ucsiBytes = [byte0, byte1, byte2, byte3, byte4, byte5, byte6, byte7];
            const aardvarkCmd = [0x09, 0x08, ...ucsiBytes];
            const aardvarkHex = aardvarkCmd.map(b => b.toString(16).padStart(2, '0').toUpperCase()).join(' ');
            commandHexInput.value = `Aardvark I2C: ${aardvarkHex}`;
            commandHexInput.dataset.rawHex = cmdHex; // Keep raw hex for backend
        } else {
            // Windows/Linux mode
            commandHexInput.value = platformInfo.is_windows ? `UcsiControl.exe send ${highDWHex} ${lowDWHex}` : `echo 0x${cmdHex} > command`;
            commandHexInput.dataset.rawHex = cmdHex;
        }
        
        // Close dialog first
        closeDialog();
        
        // Execute the command
        executeCommand();
        return; // Skip the closeDialog at the end since we already called it
        
    } else if (dialogType === 'set_usb') {
        const selected = document.querySelector('input[name="usbMode"]:checked')?.value || 'enable_usb4';
        
        // SET_USB Command format per UCSI Table 6-83:
        // Bits 0-7: Command (0x21)
        // Bits 8-15: Data Length (0x00)
        // Bits 16-22: Connector Number (7 bits)
        // Bit 23: USB3 Enable
        // Bit 24: USB4 Enable
        // Bits 25-28: Reserved (4 bits)
        // Bits 29-60: EUDO (32 bits) - set to 0 for now
        // Bits 61-63: Reserved (3 bits)
        
        const port = selectedPort;
        
        // Byte 2: Connector Number (7 bits) + USB3 bit (bit 7)
        // Byte 3: USB4 bit (bit 0) + Reserved (bits 1-7)
        // NOTE: The bits appear to be DISABLE bits (1=disable, 0=enable)
        
        let byte2, byte3;
        
        if (selected === 'enable_usb4') {
            // Enable USB4: clear both disable bits
            byte2 = port;        // USB3 disable=0, Connector=port
            byte3 = 0x00;        // USB4 disable=0
        } else if (selected === 'disable_usb4') {
            // Disable USB4: set both disable bits
            byte2 = port | 0x80; // USB3 disable=1, Connector=port
            byte3 = 0x01;        // USB4 disable=1
        } else if (selected === 'enable_usb3') {
            // Enable USB3 only: set USB4 disable bit, clear USB3 disable bit
            byte2 = port;        // USB3 disable=0, Connector=port
            byte3 = 0x01;        // USB4 disable=1
        } else if (selected === 'disable_usb3') {
            // Disable USB3: set USB3 disable bit, clear USB4 disable bit
            byte2 = port | 0x80; // USB3 disable=1, Connector=port
            byte3 = 0x00;        // USB4 disable=0
        }
        
        // Build command: little-endian format
        // For Windows: 8 bytes (00000000 + byte3 + byte2 + 0021)
        // For Linux: 4 bytes only (byte3 + byte2 + 00 + 21) as minimal hex
        let cmdHex, linuxHex;
        
        if (platformInfo.is_windows) {
            cmdHex = `00000000${byte3.toString(16).padStart(2, '0').toUpperCase()}${byte2.toString(16).padStart(2, '0').toUpperCase()}0021`;
        } else {
            // Linux: Build as 32-bit value (4 bytes): byte3 byte2 00 21
            const cmd32bit = (byte3 << 24) | (byte2 << 16) | 0x0021;
            linuxHex = cmd32bit.toString(16).toUpperCase();
            cmdHex = linuxHex; // Use Linux format for rawHex too
        }
        
        const descriptions = {
            'enable_usb4': 'Enable USB4',
            'disable_usb4': 'Disable USB4',
            'enable_usb3': 'Enable USB3',
            'disable_usb3': 'Disable USB3'
        };
        
        // Set the selectedCommand to ensure proper command_key is sent to server
        selectedCommand = '21 - SET_USB';
        selectedCommandInput.value = selectedCommand;
        
        // Update command hex input and execute
        commandHexInput.value = platformInfo.is_windows ? `UcsiControl.exe send 0 ${cmdHex}` : `echo 0x${linuxHex || cmdHex} > command`;
        commandHexInput.dataset.rawHex = cmdHex;
        
        // Close dialog first
        closeDialog();
        
        // Execute the command
        setTimeout(() => executeCommand(), 100);
        
    } else if (dialogType === 'set_new_cam') {
        const port = selectedPort.toString(); // Use globally selected port
        const action = document.getElementById('newcam_action')?.value || 'exit';
        const mode = document.getElementById('newcam_mode')?.value || '0xFF';
        const cmdHex = document.getElementById('newcam_preview')?.value || '';
        
        // Build description
        const modeNames = {
            '0xFF': 'Exit All Modes',
            '0x00': 'Reserved (Offset 0)',
            '0x01': 'DisplayPort (DP)',
            '0x02': 'Thunderbolt (TBT)',
            '0x03': 'USB4',
            '0x04': 'Custom Mode'
        };
        const actionText = action === 'enter' ? 'Enter' : 'Exit';
        const modeName = modeNames[mode] || mode;
        const description = `Port ${port} - ${actionText} ${modeName}`;
        
        // Update command hex input and execute
        const finalHex = platformInfo.is_linux ? convertWindowsHexToLinux(cmdHex) : cmdHex;
        commandHexInput.value = platformInfo.is_windows ? `UcsiControl.exe send 0 ${cmdHex}` : `echo 0x${finalHex} > command`;
        commandHexInput.dataset.rawHex = finalHex;
        
        // Close dialog first
        closeDialog();
        
        // Execute the command
        executeCommand();
        return; // Skip the closeDialog at the end since we already called it
        
    } else if (dialogType === 'connector_reset') {
        const selected = document.querySelector('input[name="resetType"]:checked')?.value || 'hard';
        // Build command hex with selected port
        // Format: [resetFlag][connectorNum]0003
        // byte0: 0x80 for hard reset, 0x00 for data reset
        // byte1: connector/port number
        // byte2: 0x00 (data length)
        // byte3: 0x03 (CONNECTOR_RESET command)
        const portHex = selectedPort.toString(16).padStart(2, '0').toUpperCase();
        const configs = {
            'hard': `80${portHex}0003`,
            'data': `00${portHex}0003`
        };
        const descriptions = {
            'hard': 'Hard Reset',
            'data': 'Data Reset'
        };
        const aardvarkCommands = {
            'hard': '3 - CONNECTOR_RESET (hard)',
            'data': '3 - CONNECTOR_RESET (soft)'
        };
        const cmdHex = configs[selected];
        
        // Set the selectedCommand to ensure proper command_key is sent to server
        selectedCommand = aardvarkMode ? aardvarkCommands[selected] : '3 - CONNECTOR_RESET';
        selectedCommandInput.value = selectedCommand;
        
        // Update command hex input
        const finalHex = platformInfo.is_linux ? convertWindowsHexToLinux(cmdHex) : cmdHex;
        commandHexInput.value = platformInfo.is_windows ? `UcsiControl.exe send 0 ${cmdHex}` : `echo 0x${finalHex} > command`;
        commandHexInput.dataset.rawHex = finalHex;
        
        // Close dialog first
        closeDialog();
        
        // Execute the command
        executeCommand();
        return; // Skip the closeDialog at the end since we already called it
        
    } else if (dialogType === 'ack_cc_ci') {
        const selected = document.querySelector('input[name="ackType"]:checked')?.value || 'both';
        
        // ACK_CC_CI format per UCSI Table 6-7:
        // Byte 0: Command (0x04)
        // Byte 1: Data Length (0x00)
        // Byte 2: Bit 0 (bit 16 overall) = Connector Change Acknowledge, Bit 1 (bit 17 overall) = Command Completed Acknowledge
        // Bytes 3-7: Reserved (0x00)
        const configs = {
            'command': '00020004',     // Bit 17 = 1 (Command Completed Acknowledge)
            'connector': '00010004',   // Bit 16 = 1 (Connector Change Acknowledge)
            'both': '00030004'         // Bits 16 and 17 = 1 (Both) - RECOMMENDED
        };
        const descriptions = {
            'command': 'Command Complete',
            'connector': 'Connector Change',
            'both': 'Both'
        };
        const cmdHex = configs[selected];
        
        // Set the selectedCommand to ensure proper command_key is sent to server
        selectedCommand = '4 - ACK_CC_CI';
        selectedCommandInput.value = selectedCommand;
        
        // Update command hex input
        const finalHex = platformInfo.is_linux ? convertWindowsHexToLinux(cmdHex) : cmdHex;
        commandHexInput.value = platformInfo.is_windows ? `UcsiControl.exe send 0 ${cmdHex}` : `echo 0x${finalHex} > command`;
        commandHexInput.dataset.rawHex = finalHex;
        
        // Close dialog first
        closeDialog();
        
        // Execute the command
        executeCommand();
        return; // Skip the closeDialog at the end since we already called it
        
    } else if (dialogType === 'retimer_mode') {
        const selected = document.querySelector('input[name="retimerMode"]:checked')?.value || 'usb';
        const configs = {
            'usb': '0101001F',
            'dp': '0201001F',
            'tbt': '0301001F',
            'usb4': '0401001F'
        };
        const descriptions = {
            'usb': 'USB Mode',
            'dp': 'DisplayPort Mode',
            'tbt': 'Thunderbolt Mode',
            'usb4': 'USB4 Mode'
        };
        const aardvarkCommands = {
            'usb': '25 - SET_RETIMER_MODE (USB)',
            'dp': '25 - SET_RETIMER_MODE (DP)',
            'tbt': '25 - SET_RETIMER_MODE (TBT)',
            'usb4': '25 - SET_RETIMER_MODE (USB4)'
        };
        const cmdHex = configs[selected];
        const fullCommandName = aardvarkMode ? aardvarkCommands[selected] : `30 - SET_RETIMER_MODE (${descriptions[selected]})`;
        selectedCommand = fullCommandName;
        selectedCommandInput.value = fullCommandName;
        showCommandExecutionInfo(cmdHex, fullCommandName);
        
    } else if (dialogType === 'run_categories') {
        const selectedCmdKeys = Array.from(document.querySelectorAll('input[name="runCmd"]:checked'))
            .map(checkbox => checkbox.value);
        
        if (selectedCmdKeys.length === 0) {
            alert('Please select at least one command.');
            return;
        }
        
        // Run selected commands directly
        runCategoriesCommands(null, selectedCmdKeys);
    } else if (dialogType === 'stress_test') {
        // Sequential test with ordered commands
        if (sequentialTestConfig.length === 0) {
            alert('Please add at least one command to the sequence.');
            return;
        }
        
        // Get selected ports
        const selectedPorts = Array.from(document.querySelectorAll('input[name="seqPort"]:checked'))
            .map(checkbox => parseInt(checkbox.value));
        
        if (selectedPorts.length === 0) {
            alert('Please select at least one port.');
            return;
        }
        
        // Get timing settings
        const commandDelay = parseInt(document.getElementById('seqCommandDelay').value);
        
        // Execute sequential test
        executeSequentialTest(sequentialTestConfig, selectedPorts, commandDelay);
    } else if (dialogType === 'concurrent_test') {
        // Get Thread 1 configuration
        const thread1Type = document.getElementById('thread1Type').value;
        const thread1Port = parseInt(document.getElementById('thread1Port').value);
        const thread1Iterations = parseInt(document.getElementById('thread1Iterations').value);
        const thread1Delay = parseInt(document.getElementById('thread1Delay').value);
        
        let thread1Config = {
            type: thread1Type,
            port: thread1Port,
            iterations: thread1Iterations,
            delay: thread1Delay
        };
        
        if (thread1Type === 'command') {
            const thread1Command = document.getElementById('thread1Command').value;
            if (!thread1Command) {
                alert('Please select a command for Thread 1');
                return;
            }
            thread1Config.command = thread1Command;
        }
        
        // Get Thread 2 configuration
        const thread2Type = document.getElementById('thread2Type').value;
        const thread2Port = parseInt(document.getElementById('thread2Port').value);
        const thread2Iterations = parseInt(document.getElementById('thread2Iterations').value);
        const thread2Delay = parseInt(document.getElementById('thread2Delay').value);
        
        let thread2Config = {
            type: thread2Type,
            port: thread2Port,
            iterations: thread2Iterations,
            delay: thread2Delay
        };
        
        if (thread2Type === 'command') {
            const thread2Command = document.getElementById('thread2Command').value;
            if (!thread2Command) {
                alert('Please select a command for Thread 2');
                return;
            }
            thread2Config.command = thread2Command;
        }
        
        // Get synchronization settings
        const syncMode = document.getElementById('syncMode').value;
        const thread2StartDelay = syncMode === 'offset' ? parseInt(document.getElementById('thread2StartDelay').value) : 0;
        
        // Execute concurrent test
        executeConcurrentTestV2(thread1Config, thread2Config, syncMode, thread2StartDelay);
    }
    
    closeDialog();
}

function showCommandExecutionInfo(cmdHex, fullCommandName) {
    // For commands that already include port info (like SET_NEW_CAM), don't modify
    // 8-char hex = full 4-byte UCSI CONTROL value, already has port embedded
    // >8 chars = extended format, already complete
    let displayHex = cmdHex;
    if (cmdHex.length < 8) {
        // Update connector number in the connector byte (3rd from last hex pair)
        // The connector is in bits [22:16], i.e., the 3rd byte from the end
        const hexBytes = cmdHex.padStart(8, '0'); // Pad to 8 chars (4 bytes)
        const byte3 = parseInt(hexBytes.substring(0, 2), 16);
        const byte2 = parseInt(hexBytes.substring(2, 4), 16);
        const byte1_0 = hexBytes.substring(4, 8);
        const newByte2 = (byte2 & 0x80) | (selectedPort & 0x7F);
        displayHex = byte3.toString(16).padStart(2, '0') +
                     newByte2.toString(16).padStart(2, '0') + byte1_0;
        // Strip leading zeros for display
        displayHex = displayHex.replace(/^0+/, '') || '0';
    }
    
    // Convert to Linux format if needed
    const linuxHex = platformInfo.is_linux ? convertWindowsHexToLinux(displayHex) : displayHex;
    const commandFormat = platformInfo.is_windows 
        ? `UcsiControl.exe send 0 ${displayHex}` 
        : `echo 0x${linuxHex} > command`;
    
    outputArea.innerHTML = `
<div style="padding: 20px; background: #f8f9fa; border-left: 4px solid #28a745; margin-bottom: 15px;">
    <h3 style="color: #2c3e50; margin-top: 0;">✅ Command Configured</h3>
    <p><strong>Command:</strong> ${fullCommandName}</p>
    <p><strong>Port:</strong> ${selectedPort}</p>
    <p><strong>Format:</strong> <code style="background: #e8f4f8; padding: 4px 8px; border-radius: 4px;">${commandFormat}</code></p>
    <hr style="border: none; border-top: 1px solid #ddd; margin: 15px 0;">
    <p><strong>Instructions:</strong></p>
    <ol style="margin: 10px 0; padding-left: 20px;">
        <li>Open a ${platformInfo.is_windows ? 'command prompt' : 'terminal'}</li>
        <li>Run the command above${platformInfo.is_windows ? ' using UcsiControl.exe' : ' (requires sudo)'}</li>
        <li>Copy the hex response from the output</li>
        <li>Paste it in the "Hex Response Data" field above</li>
        <li>Click "Decode" to see the results</li>
    </ol>
</div>`;
}

function closeDialog() {
    dialogOverlay.style.display = 'none';
}

// Show Aardvark error dialog
function showAardvarkStatusDialog(statusData) {
    // Ensure dialog elements exist
    if (!dialogTitle || !dialogContent || !dialogOk || !dialogCancel || !dialogOverlay) {
        console.error('Dialog elements not found');
        alert(statusData.message || 'Aardvark error'); // Fallback to alert
        return;
    }
    
    // Determine the title and styling based on status
    let titleText = 'Aardvark Adapter Not Ready';
    let badgeColor = '#ef4444'; // red
    let badgeText = '✕';
    let detailedMessage = statusData.message || 'Unable to access Aardvark adapter';
    
    if (statusData.status === 'driver_not_installed') {
        titleText = 'Aardvark Drivers Not Installed';
        badgeColor = '#f59e0b'; // amber
        badgeText = '⚙️';
    } else if (statusData.status === 'device_present_no_drivers') {
        titleText = 'Aardvark Device Detected (Drivers Missing)';
        badgeColor = '#f59e0b'; // amber
        badgeText = '⚠️';
    } else if (statusData.status === 'device_not_connected') {
        titleText = 'Aardvark Device Not Connected';
        badgeColor = '#ef4444'; // red
        badgeText = '✕';
    }
    
    dialogTitle.textContent = titleText;
    
    // Replace newlines with <br> and format the message
    const formattedMessage = detailedMessage.replace(/\n/g, '<br>');
    
    dialogContent.innerHTML = `
        <div style="padding: 10px 20px 20px; text-align: center; font-family: inherit;">

            <!-- Device image with status badge -->
            <div style="position: relative; display: inline-block; margin-bottom: 18px;">
                <img
                    src="https://www.totalphase.com/media/catalog/product/a/a/aardvark-black-rgb144_2.jpg"
                    alt="Aardvark I2C/SPI Host Adapter"
                    style="width: 160px; height: 160px; object-fit: contain; border-radius: 12px;
                           border: 2px solid #e2e8f0; background: #f8fafc; display: block;"
                    onerror="this.style.display='none'"
                />
                <span style="position: absolute; top: -8px; right: -8px;
                             background: ${badgeColor}; color: white; border-radius: 50%;
                             width: 34px; height: 34px; display: flex; align-items: center;
                             justify-content: center; font-size: 18px; font-weight: bold;
                             box-shadow: 0 2px 8px rgba(0,0,0,0.2);"
                      title="${statusData.status === 'driver_not_installed' ? 'Drivers not installed' : statusData.status === 'device_present_no_drivers' ? 'Device present but drivers missing' : 'Not connected'}">
                    ${badgeText}
                </span>
            </div>

            <p style="font-size: 15px; color: ${statusData.status === 'device_not_connected' ? '#dc2626' : '#b45309'}; font-weight: 600; margin: 0 0 12px;">
                ${titleText}
            </p>
            <p style="font-size: 13px; color: #64748b; margin: 0 0 18px; line-height: 1.6;">
                ${formattedMessage}
            </p>

            <div style="background: #f8fafc; padding: 14px 16px; border-radius: 8px;
                        text-align: left; border: 1px solid #e2e8f0;">
                <p style="margin: 0 0 8px; font-weight: 600; font-size: 13px; color: #1e293b;">
                    ${statusData.status === 'device_not_connected' ? 'Troubleshooting Steps:' : 'Installation Steps:'}
                </p>
                <ol style="margin: 0; padding-left: 18px; color: #475569; font-size: 13px;
                           line-height: 1.8;">
                    ${statusData.status === 'driver_not_installed' ? 
                        `<li>Download Aardvark drivers from Total Phase website</li>
                         <li>Install the drivers for your operating system</li>
                         <li>Run: <code style="background: #fff; padding: 2px 4px; border-radius: 2px;">pip install pyaardvark</code></li>
                         <li>Connect your Aardvark adapter to USB</li>
                         <li>Restart the application</li>` :
                        statusData.status === 'device_present_no_drivers' ?
                        `<li>Download Aardvark drivers from Total Phase website</li>
                         <li>In Windows Device Manager, locate the device under "Other devices" (yellow exclamation mark)</li>
                         <li>Right-click the device and select "Update driver" or "Install driver"</li>
                         <li>Complete the driver installation (it will move to "Universal Serial Bus Controllers")</li>
                         <li>Run: <code style="background: #fff; padding: 2px 4px; border-radius: 2px;">pip install pyaardvark</code></li>
                         <li>Restart the application</li>` :
                        `<li>Connect the Aardvark I2C/SPI adapter to a USB port</li>
                         <li>Wait 2-3 seconds for drivers to load</li>
                         <li>Check Device Manager for "Total Phase Aardvark" under "Universal Serial Bus Controllers"</li>
                         <li>Try enabling Aardvark Mode again</li>`
                    }
                </ol>
            </div>
        </div>
    `;
    
    // Hide Cancel button, only show OK
    dialogCancel.style.display = 'none';
    dialogOk.textContent = 'OK';
    
    // Set up one-time OK handler
    const okHandler = function() {
        closeDialog();
        dialogCancel.style.display = 'inline-block';
        dialogOk.removeEventListener('click', okHandler);
    };
    
    dialogOk.addEventListener('click', okHandler);
    openDialog();
}

function showAardvarkErrorDialog(errorMessage) {
    // Ensure dialog elements exist
    if (!dialogTitle || !dialogContent || !dialogOk || !dialogCancel || !dialogOverlay) {
        console.error('Dialog elements not found');
        alert(errorMessage); // Fallback to alert
        return;
    }
    
    dialogTitle.textContent = 'Aardvark Device Not Connected';
    
    dialogContent.innerHTML = `
        <div style="padding: 10px 20px 20px; text-align: center; font-family: inherit;">

            <!-- Device image with not-connected badge -->
            <div style="position: relative; display: inline-block; margin-bottom: 18px;">
                <img
                    src="https://www.totalphase.com/media/catalog/product/a/a/aardvark-black-rgb144_2.jpg"
                    alt="Aardvark I2C/SPI Host Adapter"
                    style="width: 160px; height: 160px; object-fit: contain; border-radius: 12px;
                           border: 2px solid #e2e8f0; background: #f8fafc; display: block;"
                    onerror="this.style.display='none'"
                />
                <span style="position: absolute; top: -8px; right: -8px;
                             background: #ef4444; color: white; border-radius: 50%;
                             width: 34px; height: 34px; display: flex; align-items: center;
                             justify-content: center; font-size: 18px; font-weight: bold;
                             box-shadow: 0 2px 8px rgba(239,68,68,0.5);"
                      title="Not connected">✕</span>
            </div>

            <p style="font-size: 15px; color: #dc2626; font-weight: 600; margin: 0 0 6px;">
                Aardvark I2C/SPI Adapter Not Detected
            </p>
            <p style="font-size: 13px; color: #64748b; margin: 0 0 18px; line-height: 1.5;">
                ${errorMessage}
            </p>

            <div style="background: #f8fafc; padding: 14px 16px; border-radius: 8px;
                        text-align: left; border: 1px solid #e2e8f0;">
                <p style="margin: 0 0 8px; font-weight: 600; font-size: 13px; color: #1e293b;">
                    To enable Aardvark Mode:
                </p>
                <ol style="margin: 0; padding-left: 18px; color: #475569; font-size: 13px;
                           line-height: 1.8;">
                    <li>Plug the Aardvark adapter into a USB port</li>
                    <li>Install the adapter driver package from its vendor support page</li>
                    <li>Verify it appears in Windows Device Manager</li>
                    <li>Confirm the Aardvark Python library is installed</li>
                </ol>
            </div>
        </div>
    `;
    
    // Hide Cancel button, only show OK
    dialogCancel.style.display = 'none';
    dialogOk.textContent = 'OK';
    
    // Set up one-time OK handler
    const okHandler = function() {
        closeDialog();
        dialogCancel.style.display = 'inline-block';
        dialogOk.removeEventListener('click', okHandler);
    };
    dialogOk.addEventListener('click', okHandler);
    
    dialogOverlay.style.display = 'flex';
}

// Device Manager Check
function fetchPlatformInfo() {
    // Fetch platform information from backend
    fetch('/api/platform-info')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                platformInfo = data;
                console.log('Platform detected:', platformInfo.platform);
                console.log('UCSI path:', platformInfo.ucsi_path);
                console.log('Aardvark available:', data.aardvark_available);
                console.log('Aardvark detected:', data.aardvark_detected);
                
                // Update command display based on platform
                updateCommandDisplay();
                
                // Show sudo dialog if on Linux and authentication needed
                if (data.needs_sudo_auth) {
                    console.log('Linux detected - showing sudo authentication dialog');
                    setTimeout(() => showSudoDialog(), 500); // Small delay for better UX
                } else {
                    // On Windows or if Linux auth already done, check device manager
                    if (!platformInfo.is_linux) {
                        checkDeviceManager();
                    }
                }
            }
        })
        .catch(error => {
            console.error('Failed to fetch platform info:', error);
        });
}

function updateCommandDisplay() {
    // Update all command items to show platform-specific format
    const commandItems = document.querySelectorAll('.command-item');
    
    commandItems.forEach(item => {
        const cmdHex = item.dataset.cmdHex;
        const hexDiv = item.querySelector('.command-hex');
        
        if (platformInfo.is_linux) {
            // Linux format: Just show hex value with 0x prefix
            hexDiv.innerHTML = `<small style="color: #fff;">0x${cmdHex}</small>`;
            hexDiv.style.fontSize = '0.85em';
            hexDiv.style.wordBreak = 'normal';
        } else {
            // Windows format: Just show the hex value
            hexDiv.innerHTML = `<small style="color: #fff;">${cmdHex}</small>`;
            hexDiv.style.fontSize = '0.85em';
        }
    });
}

function getCommandForPlatform(cmdHex) {
    // Generate platform-specific command string
    if (platformInfo.is_linux) {
        return {
            write: `echo 0x${cmdHex} > command`,
            read: 'cat response',
            basePath: platformInfo.ucsi_path || '/sys/kernel/debug/usb/ucsi/USBC000:00'
        };
    } else {
        return {
            command: `UcsiControl.exe Send 0 ${cmdHex}`
        };
    }
}

// Device Manager Check
function checkDeviceManager() {
    const statusDiv = document.getElementById('deviceStatus');
    if (!statusDiv) return;
    
    // Skip device manager check on Linux
    if (platformInfo.is_linux) {
        console.log('Skipping device manager check on Linux');
        return;
    }
    
    // Show checking status
    statusDiv.innerHTML = '<span class="status-icon">🔍</span><span class="status-text">Checking UCSI device status...</span>';
    statusDiv.style.background = '#f8f9fa';
    statusDiv.style.borderColor = '#dee2e6';
    
    // Call backend to check device
    fetch('/api/check_device')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const status = data.device_status;
                
                // Build status message
                let message = '';
                let icon = '';
                let bgColor = '';
                let borderColor = '';
                
                // Check if we have the new UCSI message format
                if (status.ucsi_message) {
                    // Use the message from backend
                    if (status.device_found) {
                        icon = '✓';
                        message = `<strong style="color: #28a745;">${status.ucsi_message}</strong>`;
                        // Don't show the path for Linux
                        bgColor = '#d4edda';
                        borderColor = '#28a745';
                    } else {
                        icon = '⚠️';
                        message = `<strong style="color: #dc3545;">${status.ucsi_message}</strong>`;
                        if (status.error) {
                            message += `<br><small>${status.error}</small>`;
                        }
                        bgColor = '#fff3cd';
                        borderColor = '#ffc107';
                    }
                } else if (status.error) {
                    icon = '⚠️';
                    message = `Device check error: <strong style="color: #dc3545;">${status.error}</strong>`;
                    bgColor = '#fff3cd';
                    borderColor = '#ffc107';
                } else if (!status.device_found) {
                    icon = '⚠️';
                    message = '<strong style="color: #dc3545;">WARNING: UCSI device not found in Device Manager</strong>';
                    bgColor = '#fff3cd';
                    borderColor = '#ffc107';
                } else if (status.yellow_bang || status.has_warning) {
                    icon = '⚠️';
                    let problemText = '';
                    if (status.problem_code !== null && status.problem_code !== undefined) {
                        problemText = ` (Problem Code: ${status.problem_code})`;
                    }
                    const deviceName = status.device_name || 'UCSI Device';
                    message = `<strong style="color: #f59e0b;">⚠️ WARNING: ${deviceName} has Yellow Bang${problemText}</strong>`;
                    if (status.status_text && status.status_text !== 'Unknown') {
                        message += `<br><small>Status: ${status.status_text}</small>`;
                    }
                    message += `<br><small>FW: ${status.firmware_version}</small>`;
                    message += `<br><small style="color: #dc3545;"><strong>Device has driver issues - check Device Manager</strong></small>`;
                    bgColor = '#fff3cd';
                    borderColor = '#f59e0b';
                } else if (status.has_error) {
                    icon = '❌';
                    const deviceName = status.device_name || 'UCSI Device';
                    message = `<strong style="color: #dc3545;">ERROR: ${deviceName} has error status</strong>`;
                    if (status.status_text && status.status_text !== 'Unknown') {
                        message += `<br><small>Status: ${status.status_text}</small>`;
                    }
                    message += `<br><small>FW: ${status.firmware_version}</small>`;
                    bgColor = '#f8d7da';
                    borderColor = '#dc3545';
                } else {
                    icon = '✓';
                    const deviceName = status.device_name || 'UCSI Device';
                    const fwVersion = status.firmware_version;
                    // Check if firmware version is "Not Available" or contains "Error"
                    if (fwVersion === 'Not Available' || fwVersion.includes('Error')) {
                        message = `<strong style="color: #28a745;">Ready - ${deviceName} OK (No Yellow Bang)</strong><br><small>FW: <span style="color: #dc3545;">${fwVersion}</span></small>`;
                    } else {
                        message = `<strong style="color: #28a745;">Ready - ${deviceName} OK (No Yellow Bang)</strong><br><small>FW: ${fwVersion}</small>`;
                    }
                    
                    // Add Aardvark status information
                    if (platformInfo.aardvark_available && platformInfo.aardvark_detected) {
                        message += '<br><small><span style="color: #28a745;">✓ Aardvark I2C/SPI Adapter Detected</span></small>';
                    } else if (platformInfo.aardvark_available && !platformInfo.aardvark_detected) {
                        message += '<br><small><span style="color: #ffc107;">⚠️ Aardvark Library Available But No Device Detected</span></small>';
                    }
                    
                    bgColor = '#d4edda';
                    borderColor = '#28a745';
                }
                
                statusDiv.innerHTML = `<span class="status-icon">${icon}</span><span class="status-text">${message}</span>`;
                statusDiv.style.background = bgColor;
                statusDiv.style.borderColor = borderColor;
                
                // Log detailed status to console
                console.log('Device Manager Check Results:', status);
                
                // After device check, automatically detect number of ports (Windows only)
                if (!platformInfo.is_linux) {
                    console.log('⏰ Scheduling auto port detection in 300ms...');
                    setTimeout(() => {
                        console.log('⏰ Timer fired, calling autoDetectPorts()...');
                        autoDetectPorts();
                    }, 300);
                }
            }
        })
        .catch(error => {
            console.error('Device check failed:', error);
            statusDiv.innerHTML = '<span class="status-icon">⚠️</span><span class="status-text"><strong style="color: #dc3545;">Device check failed - ' + error.message + '</strong></span>';
            statusDiv.style.background = '#fff3cd';
            statusDiv.style.borderColor = '#ffc107';
        });
}

// Automatically detect number of ports by running GET_CAPABILITY
// Similar to desktop GUI's _detect_num_connectors() method
function autoDetectPorts() {
    console.log('========================================');
    console.log('AUTO-DETECT PORTS: Starting...');
    console.log('========================================');
    
    // Find the GET_CAPABILITY command from the DOM
    const commandItems = document.querySelectorAll('.command-item');
    let capabilityElement = null;
    
    commandItems.forEach(item => {
        if (item.dataset.cmdKey === '6 - GET_CAPABILITY') {
            capabilityElement = item;
        }
    });
    
    if (!capabilityElement) {
        console.error('❌ AUTO-DETECT: GET_CAPABILITY command not found in DOM');
        return;
    }
    
    const commandKey = capabilityElement.dataset.cmdKey;
    const commandHex = capabilityElement.dataset.cmdHex;  // Get raw hex from data attribute
    
    console.log('✓ Found GET_CAPABILITY command');
    console.log('  Command Key:', commandKey);
    console.log('  Command Hex:', commandHex);
    
    const statusDiv = document.getElementById('deviceStatus');
    
    // Prepare the request
    const payload = {
        command_key: commandKey,
        command_hex: commandHex,
        port: 0,  // Port 0 for GET_CAPABILITY
        ucsi_version: detectedVersion,
        aardvark_mode: aardvarkMode
    };
    
    console.log('📤 Sending request to /api/execute_command:');
    console.log('  Payload:', JSON.stringify(payload, null, 2));
    
    // Call the execute endpoint to run GET_CAPABILITY and get response
    fetch('/api/execute_command', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
    .then(response => {
        console.log('📥 Received response from /api/execute_command');
        return response.json();
    })
    .then(data => {
        console.log('📊 Response data:', JSON.stringify(data, null, 2));
        console.log('  Success:', data.success);
        console.log('  Error:', data.error);
        console.log('  Hex Response:', data.hex_response);
        console.log('  Decoded Data:', data.decoded);
        console.log('  Raw Output:', data.raw_output);
        
        if (data.success && data.decoded) {
            // Extract number of connectors from the response
            let portCount = 0;
            
            console.log('🔍 Extracting port count...');
            console.log('  Decoded data type:', typeof data.decoded);
            console.log('  Decoded data keys:', Object.keys(data.decoded));
            console.log('  Full decoded structure:', JSON.stringify(data.decoded, null, 2));
            
            // First try to parse from raw_output text
            if (data.raw_output) {
                console.log('  🔎 Searching raw_output for bNumConnectors...');
                const match = data.raw_output.match(/bNumConnectors[:\s]+(\d+)/i);
                if (match && match[1]) {
                    portCount = parseInt(match[1]);
                    console.log('  ✓ From raw_output bNumConnectors:', portCount);
                } else {
                    console.log('  ⚠️ bNumConnectors not found in raw_output');
                }
            }
            
            // Try multiple possible field names in decoded data
            if (portCount === 0 && data.decoded['bNumConnectors']) {
                portCount = parseInt(data.decoded['bNumConnectors']);
                console.log('  ✓ From decoded["bNumConnectors"]:', portCount);
            }
            
            // Check if data is structured with fields array (UCSI 3.0 format)
            if (portCount === 0 && data.decoded.fields && Array.isArray(data.decoded.fields)) {
                console.log('  🔎 Searching in fields array...');
                for (const field of data.decoded.fields) {
                    if (field.field === 'bNumConnectors') {
                        portCount = parseInt(field.value);
                        console.log('  ✓ From fields array bNumConnectors:', portCount);
                        break;
                    }
                }
            }
            
            if (portCount === 0) {
                console.log('  ⚠️ Port count field not found in decoded data');
                console.log('  Available keys:', Object.keys(data.decoded));
                
                // Try to search all values recursively
                console.log('  🔎 Searching for connectors field recursively...');
                const searchForConnectors = (obj, path = '') => {
                    for (let key in obj) {
                        const currentPath = path ? `${path}.${key}` : key;
                        if (key.toLowerCase().includes('connector') || key.toLowerCase().includes('numconnector')) {
                            console.log(`    Found at ${currentPath}:`, obj[key]);
                            if (typeof obj[key] === 'number' || typeof obj[key] === 'string') {
                                const val = parseInt(obj[key]);
                                if (val > 0) {
                                    portCount = val;
                                }
                            }
                        }
                        if (typeof obj[key] === 'object' && obj[key] !== null) {
                            searchForConnectors(obj[key], currentPath);
                        }
                    }
                };
                searchForConnectors(data.decoded);
            }
            
            if (portCount === 0 && data.hex_response) {
                // Fallback: parse from raw hex (byte 4 bits 0-6 contains number of connectors)
                const cleanHex = data.hex_response.replace(/[^0-9a-fA-F]/g, '');
                console.log('  Trying fallback hex parsing...');
                console.log('  Clean Hex:', cleanHex);
                console.log('  Hex Length:', cleanHex.length);
                
                if (cleanHex.length >= 10) {
                    // Byte 4 (index 8-9) contains number of connectors in bits 0-6
                    const byte4 = cleanHex.substring(8, 10);
                    const byte4Value = parseInt(byte4, 16);
                    portCount = byte4Value & 0x7F;  // Extract bits 0-6 (mask with 0x7F)
                    console.log('  Byte 4 (hex):', byte4);
                    console.log('  Byte 4 (decimal):', byte4Value);
                    console.log('  Port count (masked with 0x7F):', portCount);
                } else {
                    console.log('  ❌ Hex string too short for parsing (need at least 10 chars)');
                }
            }
            
            console.log('🎯 Final port count:', portCount);
            
            if (portCount > 0) {
                const maxVisiblePorts = getMaxVisiblePorts();
                const visiblePortCount = Math.min(portCount, maxVisiblePorts);
                console.log('✅ Port count valid, updating UI...');
                numDetectedPorts = visiblePortCount;
                console.log('  numDetectedPorts set to:', numDetectedPorts);
                updatePortButtonStates();
                updateRunCommandButton();
                
                // Update status message to include port count
                if (statusDiv) {
                    const currentText = statusDiv.querySelector('.status-text');
                    if (currentText) {
                        const currentHTML = currentText.innerHTML;
                        // Update the status message to include detected ports
                        // Check for both "Ready" (old format) and "found" (new format)
                        if (currentHTML.includes('Ready')) {
                            // Old format: Replace "Ready" with "Ready - Detected X port(s)"
                            currentText.innerHTML = currentHTML.replace('Ready', `Ready - Detected ${portCount} port(s)`);
                            console.log('  ✓ Updated status message (Ready format)');
                        } else if (currentHTML.includes('found in Device Manager') || currentHTML.includes('enabled in debugfs')) {
                            // New format: Append port info or replace existing port info
                            if (currentHTML.includes('Detected')) {
                                // Replace existing port count
                                currentText.innerHTML = currentHTML.replace(/Detected \d+ port\(s\)/, `Detected ${portCount} port(s)`);
                            } else {
                                // Add port count
                                currentText.innerHTML = currentHTML.replace('</strong>', ` - Detected ${portCount} port(s)</strong>`);
                            }
                            console.log('  ✓ Updated status message (new format)');
                        }
                    }
                }
                
                console.log(`✅ AUTO-DETECT COMPLETE: ${visiblePortCount}/${portCount} port(s) enabled`);
            } else {
                console.warn('❌ Invalid port count:', portCount, '(must be >= 1)');
                if (statusDiv) {
                    statusDiv.innerHTML = '<span class="status-icon">⚠️</span><span class="status-text"><strong style="color: #dc3545;">UCSI device found, but GET_CAPABILITY returned 0 connectors.</strong><br><small>Run command 6 - GET_CAPABILITY manually and verify MESSAGE_IN/CCI values.</small></span>';
                    statusDiv.style.background = '#fff3cd';
                    statusDiv.style.borderColor = '#ffc107';
                }
            }
        } else {
            console.warn('❌ Auto port detection failed');
            console.warn('  Success:', data.success);
            console.warn('  Error:', data.error);
            console.warn('  Has decoded data:', !!data.decoded);
            
            // Check if it's a "No UCSI device found" error
            if (data.output && data.output.includes('No UCSI device found')) {
                console.log('✓ Detected "No UCSI device found" error, updating device status banner');
                // Update device status banner at the top
                const statusDiv = document.getElementById('deviceStatus');
                if (statusDiv) {
                    statusDiv.innerHTML = '<span class="status-icon">❌</span><span class="status-text"><strong style="color: #dc3545;">No UCSI device found</strong></span>';
                    statusDiv.style.background = '#f8d7da';
                    statusDiv.style.borderColor = '#dc3545';
                    console.log('✓ Device status banner updated to show No UCSI device error');
                } else {
                    console.error('❌ deviceStatus element not found');
                }
            } else if (statusDiv) {
                const errorText = data.error || 'GET_CAPABILITY failed';
                statusDiv.innerHTML = `<span class="status-icon">⚠️</span><span class="status-text"><strong style="color: #dc3545;">UCSI device found, but port detection failed.</strong><br><small>${errorText}</small></span>`;
                statusDiv.style.background = '#fff3cd';
                statusDiv.style.borderColor = '#ffc107';
            }
        }
        console.log('========================================');
    })
    .catch(error => {
        console.error('❌ AUTO-DETECT ERROR:', error);
        console.error('  Error message:', error.message);
        console.error('  Error stack:', error.stack);
        console.log('========================================');
    });
}


// ===== BATCH OPERATIONS AND RESULTS SUMMARY =====

// Initialize Chart.js pie chart
function initializeChart() {
    const ctx = resultsChart.getContext('2d');
    pieChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Passed', 'Failed', 'Not Run'],
            datasets: [{
                data: [0, 0, 0],
                backgroundColor: [
                    '#10b981',  // Green for passed
                    '#ef4444',  // Red for failed
                    '#94a3b8'   // Gray for not run
                ],
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        font: {
                            size: 13
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
    
    // Show chart immediately with default values
    updateResultsChart();
}

// Update pie chart with current results
function updateResultsChart() {
    if (!pieChart) return;
    
    // Get results based on current filter (all ports or specific port)
    let displayResults;
    if (currentViewPort === 'all') {
        displayResults = testResults;
    } else {
        const port = parseInt(currentViewPort);
        displayResults = portResults[port] || { passed: 0, failed: 0, notRun: 0, total: 0, details: [] };
    }
    
    // Always show the chart
    pieChart.data.datasets[0].data = [
        displayResults.passed,
        displayResults.failed,
        displayResults.notRun
    ];
    pieChart.update();
    
    resultsChart.classList.add('active');
    chartMessage.style.display = 'none';
    
    // Update stats with port indicator
    const portLabel = currentViewPort === 'all' ? 'All Ports' : `Port ${currentViewPort}`;
    const statsContainer = document.getElementById('resultsStats');
    statsContainer.innerHTML = `
        <div class="stat-item passed">
            <div class="stat-value">${displayResults.passed}</div>
            <div class="stat-label">Passed</div>
        </div>
        <div class="stat-item failed">
            <div class="stat-value">${displayResults.failed}</div>
            <div class="stat-label">Failed</div>
        </div>
        <div class="stat-item not-run">
            <div class="stat-value">${displayResults.notRun}</div>
            <div class="stat-label">Not Run</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">${displayResults.total}</div>
            <div class="stat-label">Total (${portLabel})</div>
        </div>
    `;
}

// Run all commands sequentially
async function runAllCommands() {
    if (!confirm('This will run all UCSI commands sequentially. This may take several minutes. Continue?')) {
        return;
    }
    
    const allCommands = Array.from(document.querySelectorAll('.command-item'));
    
    // Reset results and accumulated decoded results
    allDecodedResults = []; // Clear accumulated results for fresh batch
    testResults = {
        passed: 0,
        failed: 0,
        notRun: 0,
        total: allCommands.length,
        details: []
    };
    
    outputArea.innerHTML = '<div style="padding: 20px;"><h3>Running All Commands...</h3><p>This may take a while. Please wait...</p></div>';
    
    for (let i = 0; i < allCommands.length; i++) {
        const cmdElement = allCommands[i];
        const cmdKey = cmdElement.dataset.cmdKey;
        
        outputArea.innerHTML += `<p>Running ${i + 1}/${allCommands.length}: ${cmdKey} on Port ${selectedPort}...</p>`;
        
        // Send ACK_CC_CI before each command (except first) to clear previous command completion state
        // This prevents "command failed" errors when running multiple commands in sequence
        if (i > 0) {
            await sendAckCcCi();
            await new Promise(resolve => setTimeout(resolve, 500));
        }
        
        // Simulate command execution
        const result = await simulateCommandExecution(cmdKey);
        
        // Track in global results
        testResults.details.push({
            command: cmdKey,
            port: selectedPort,
            status: result.status,
            message: result.message
        });
        
        // Track in port-specific results
        if (!portResults[selectedPort]) {
            portResults[selectedPort] = { passed: 0, failed: 0, notRun: 0, total: 0, details: [] };
        }
        portResults[selectedPort].details.push({
            command: cmdKey,
            status: result.status,
            message: result.message
        });
        portResults[selectedPort].total++;
        
        if (result.status === 'PASSED') {
            testResults.passed++;
            portResults[selectedPort].passed++;
        } else if (result.status === 'FAILED') {
            testResults.failed++;
            portResults[selectedPort].failed++;
        } else {
            testResults.notRun++;
            portResults[selectedPort].notRun++;
        }
        
        // Delay between commands to ensure UCSI controller is ready
        await new Promise(resolve => setTimeout(resolve, 300));
    }
    
    outputArea.innerHTML = `
        <div style="padding: 20px; background: #f8f9fa; border-left: 4px solid #2563eb;">
            <h3>✅ All Commands Completed</h3>
            <p><strong>Total Commands:</strong> ${testResults.total}</p>
            <p style="color: #10b981;"><strong>Passed:</strong> ${testResults.passed}</p>
            <p style="color: #ef4444;"><strong>Failed:</strong> ${testResults.failed}</p>
            <p style="color: #64748b;"><strong>Not Run:</strong> ${testResults.notRun}</p>
        </div>
    `;
    
    // Show Save All Results PDF button
    if (saveAllResultsPDFBtn && allDecodedResults.length > 0) {
        saveAllResultsPDFBtn.style.display = 'inline-block';
    }
    
    // Show save/copy buttons after batch completion
    updateSaveButtonText();
    const saveResultBtnGroup = document.getElementById('saveResultBtnGroup');
    if (saveResultBtnGroup) saveResultBtnGroup.style.display = 'inline-flex';
    if (copyResultBtn) copyResultBtn.style.display = 'inline-block';
    
    updateResultsChart();
    showResultsSummary();
}

// Run selected commands
function runSelectedCategories() {
    // Get all commands grouped by category
    const allCommands = Array.from(document.querySelectorAll('.command-item'));
    
    if (allCommands.length === 0) {
        alert('No commands available.');
        return;
    }
    
    // Group commands by category
    const commandsByCategory = {};
    allCommands.forEach(cmd => {
        const cat = cmd.dataset.category || 'Other';
        if (!commandsByCategory[cat]) commandsByCategory[cat] = [];
        commandsByCategory[cat].push(cmd);
    });
    
    // Create dialog to select individual commands
    const dialogContent = document.getElementById('dialogContent');
    dialogTitle.textContent = 'Select Commands to Run';
    
    let html = '<div style="padding: 10px; max-height: 60vh; overflow-y: auto;">';
    html += '<div style="margin-bottom: 12px; display: flex; gap: 10px;">';
    html += '<button type="button" onclick="document.querySelectorAll(\'input[name=runCmd]\').forEach(c=>c.checked=true)" style="padding: 4px 10px; font-size: 12px; cursor: pointer; border: 1px solid #cbd5e1; border-radius: 4px; background: #f1f5f9;">Select All</button>';
    html += '<button type="button" onclick="document.querySelectorAll(\'input[name=runCmd]\').forEach(c=>c.checked=false)" style="padding: 4px 10px; font-size: 12px; cursor: pointer; border: 1px solid #cbd5e1; border-radius: 4px; background: #f1f5f9;">Deselect All</button>';
    html += '</div>';
    
    Object.keys(commandsByCategory).forEach(category => {
        html += `<div style="margin-bottom: 8px;">`;
        html += `<div style="font-weight: 600; font-size: 13px; color: #475569; margin-bottom: 4px; padding: 4px 0; border-bottom: 1px solid #e2e8f0;">${category}</div>`;
        commandsByCategory[category].forEach(cmd => {
            const cmdKey = cmd.dataset.cmdKey;
            html += `
                <div style="margin-bottom: 4px; padding-left: 8px;">
                    <label style="display: flex; align-items: center; cursor: pointer; font-size: 13px;">
                        <input type="checkbox" name="runCmd" value="${cmdKey}" style="margin-right: 8px;">
                        <span>${cmdKey}</span>
                    </label>
                </div>
            `;
        });
        html += `</div>`;
    });
    
    html += '</div>';
    dialogContent.innerHTML = html;
    dialogOverlay.style.display = 'flex';
    dialogOverlay.dataset.type = 'run_categories';
}

// Run commands from selected categories or selected command keys
async function runCategoriesCommands(selectedCategories, selectedCmdKeys) {
    let commands;
    if (selectedCmdKeys && selectedCmdKeys.length > 0) {
        // Direct command keys selection
        commands = Array.from(document.querySelectorAll('.command-item'))
            .filter(cmd => selectedCmdKeys.includes(cmd.dataset.cmdKey));
    } else {
        // Category-based selection (legacy)
        commands = Array.from(document.querySelectorAll('.command-item'))
            .filter(cmd => selectedCategories.includes(cmd.dataset.category));
    }
    
    if (commands.length === 0) {
        alert('No commands found for selection.');
        return;
    }
    
    if (!confirm(`This will run ${commands.length} commands from selected categories. Continue?`)) {
        return;
    }
    
    // Reset results and accumulated decoded results
    allDecodedResults = []; // Clear accumulated results for fresh batch
    testResults = {
        passed: 0,
        failed: 0,
        notRun: 0,
        total: commands.length,
        details: []
    };
    
    outputArea.innerHTML = `<div style="padding: 20px;"><h3>Running Selected Categories...</h3><p>Running ${commands.length} commands. Please wait...</p></div>`;
    
    for (let i = 0; i < commands.length; i++) {
        const cmdElement = commands[i];
        const cmdKey = cmdElement.dataset.cmdKey;
        
        outputArea.innerHTML += `<p>Running ${i + 1}/${commands.length}: ${cmdKey} on Port ${selectedPort}...</p>`;
        
        // Send ACK_CC_CI before each command to clear previous command completion state
        // This prevents "command failed" errors when running multiple commands in sequence
        if (i > 0) {
            await sendAckCcCi();
            await new Promise(resolve => setTimeout(resolve, 500));
        }
        
        const result = await simulateCommandExecution(cmdKey);
        
        // Track in global results
        testResults.details.push({
            command: cmdKey,
            port: selectedPort,
            status: result.status,
            message: result.message
        });
        
        // Track in port-specific results
        if (!portResults[selectedPort]) {
            portResults[selectedPort] = { passed: 0, failed: 0, notRun: 0, total: 0, details: [] };
        }
        portResults[selectedPort].details.push({
            command: cmdKey,
            status: result.status,
            message: result.message
        });
        portResults[selectedPort].total++;
        
        if (result.status === 'PASSED') {
            testResults.passed++;
            portResults[selectedPort].passed++;
        } else if (result.status === 'FAILED') {
            testResults.failed++;
            portResults[selectedPort].failed++;
        } else {
            testResults.notRun++;
            portResults[selectedPort].notRun++;
        }
        
        await new Promise(resolve => setTimeout(resolve, 300));
    }
    
    outputArea.innerHTML = `
        <div style="padding: 20px; background: #f8f9fa; border-left: 4px solid #2563eb;">
            <h3>✅ Selected Categories Completed</h3>
            <p><strong>Total Commands:</strong> ${testResults.total}</p>
            <p style="color: #10b981;"><strong>Passed:</strong> ${testResults.passed}</p>
            <p style="color: #ef4444;"><strong>Failed:</strong> ${testResults.failed}</p>
            <p style="color: #64748b;"><strong>Not Run:</strong> ${testResults.notRun}</p>
        </div>
    `;
    
    // Show save/copy buttons after batch completion
    updateSaveButtonText();
    if (saveAllResultsPDFBtn && allDecodedResults.length > 0) {
        saveAllResultsPDFBtn.style.display = 'inline-block';
    }
    const saveResultBtnGroup = document.getElementById('saveResultBtnGroup');
    if (saveResultBtnGroup) saveResultBtnGroup.style.display = 'inline-flex';
    if (copyResultBtn) copyResultBtn.style.display = 'inline-block';
    
    updateResultsChart();
    showResultsSummary();
}

// Helper function to send ACK_CC_CI command to clear previous command completion
async function sendAckCcCi() {
    try {
        // Build ACK_CC_CI command hex (acknowledge both command complete and connector change)
        // Format: 00 03 00 04 (acknowledges both bits 16 and 17)
        const ackHex = `00030004`; // ACK both Command Complete and Connector Change
        
        // Silent execution - don't update UI
        const response = await fetch('/api/execute_command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                command_key: '4 - ACK_CC_CI',
                command_hex: ackHex,
                port: selectedPort,
                ucsi_version: detectedVersion,
                aardvark_mode: aardvarkMode
            })
        });
        
        // Don't care about the result, just send it
        await response.json();
    } catch (error) {
        console.log('ACK_CC_CI failed (non-critical):', error);
    }
}

// Simulate command execution (placeholder for actual execution)
async function simulateCommandExecution(cmdKey, port = selectedPort) {
    // Actually execute the command using the real backend API
    return await executeCommandAsync(cmdKey, port);
}

// Execute command asynchronously and return result
async function executeCommandAsync(cmdKey, port) {
    // VENDOR_DEFINED requires the 255-byte VDC loopback API — not /api/execute_command
    if (cmdKey.includes('VENDOR_DEFINED')) {
        try {
            const response = await fetch('/api/vdc_loopback_test', { method: 'POST' });
            const data = await response.json();
            if (data.decoded) {
                allDecodedResults.push({
                    command: cmdKey,
                    port: port,
                    timestamp: new Date().toLocaleString(),
                    decoded: data.decoded,
                    hex_response: data.hex_response
                });
            }
            const passed = data.success;
            return {
                status: passed ? 'PASSED' : 'FAILED',
                message: data.summary || (passed ? 'VDC loopback passed' : 'VDC loopback failed'),
                decoded: data.decoded || {},
                hex_response: data.hex_response || ''
            };
        } catch (err) {
            return {
                status: 'FAILED',
                message: 'VDC loopback request error: ' + err.message,
                decoded: { error: err.message }
            };
        }
    }

    try {
        // Format the command hex properly using the API
        // This ensures port number and all parameters are correctly set
        let cmdHex = '';
        
        try {
            const formatResponse = await fetch('/api/format_command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    command_key: cmdKey,
                    port: port,
                    aardvark_mode: aardvarkMode
                })
            });
            
            const formatData = await formatResponse.json();
            
            if (formatData.success) {
                // Use ucsi_command which has the properly formatted hex
                cmdHex = formatData.ucsi_command;
            } else {
                console.warn(`Failed to format command ${cmdKey}: ${formatData.error}`);
                return {
                    status: 'FAILED',
                    message: 'Failed to format command hex',
                    decoded: { error: formatData.error || 'Command formatting failed' }
                };
            }
        } catch (formatError) {
            console.error(`Error formatting command ${cmdKey}:`, formatError);
            return {
                status: 'FAILED',
                message: 'Error formatting command',
                decoded: { error: formatError.message }
            };
        }
        
        // If still no command hex, fail early
        if (!cmdHex) {
            return {
                status: 'FAILED',
                message: 'Command hex not found',
                decoded: { error: 'Command hex not available for batch execution' }
            };
        }
        
        // Prepare payload
        const payload = {
            command_key: cmdKey,
            command_hex: cmdHex,
            port: port,
            ucsi_version: detectedVersion,
            aardvark_mode: aardvarkMode
        };
        
        console.log(`[RunAll] Executing ${cmdKey} on port ${port} with hex: ${cmdHex}`);
        
        // Execute command via API
        const response = await fetch('/api/execute_command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Add to accumulated results with metadata
            allDecodedResults.push({
                command: cmdKey,
                port: port,
                timestamp: new Date().toLocaleString(),
                decoded: data.decoded,
                hex_response: data.hex_response
            });
            
            // Check if there's an error in decoded data
            // Check both error key and ErrorIndicator field (bit 30 of CCI)
            const hasError = (data.decoded && data.decoded.error) || 
                           (data.decoded && data.decoded.ErrorIndicator && data.decoded.ErrorIndicator !== 0);
            
            // Check if command is optional and failed
            let status = hasError ? 'FAILED' : 'PASSED';
            let message = hasError ? (data.decoded.error || 'Error Indicator set in CCI') : 'Command executed successfully';
            
            if (hasError) {
                const optionalCheck = isCommandOptional(cmdKey);
                if (optionalCheck.isOptional) {
                    status = 'NOT RUN';
                    message = `Not Implemented - ${optionalCheck.note}`;
                    data.decoded.optional_info = optionalCheck.note;
                    data.decoded.status_override = 'Not Implemented - ' + optionalCheck.note;
                }
            }
            
            return {
                status: status,
                message: message,
                decoded: data.decoded,
                hex_response: data.hex_response
            };
        } else {
            return {
                status: 'FAILED',
                message: data.error || 'Command execution failed',
                decoded: { error: data.error || 'Command execution failed' },
                output: data.output
            };
        }
    } catch (error) {
        console.error('Execute error:', error);
        return {
            status: 'FAILED',
            message: `Error: ${error.message}`,
            decoded: { error: error.message }
        };
    }
}

// Show results summary
function showResultsSummary() {
    if (testResults.total === 0) {
        alert('No test results available. Run commands first.');
        return;
    }
    
    updateResultsChart();
    
    // Scroll to results section
    const resultsSection = document.querySelector('.results-summary');
    if (resultsSection) {
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    
    // Get results based on current filter
    let displayResults;
    let portLabel;
    if (currentViewPort === 'all') {
        displayResults = testResults;
        portLabel = 'All Ports';
    } else {
        const port = parseInt(currentViewPort);
        displayResults = portResults[port] || { passed: 0, failed: 0, notRun: 0, total: 0, details: [] };
        portLabel = `Port ${currentViewPort}`;
    }
    
    // Also show detailed results in output
    let detailsHTML = `
        <div style="padding: 20px; background: #f8f9fa;">
            <h3>📊 Detailed Results Summary - ${portLabel}</h3>
            <p><strong>Total Commands:</strong> ${displayResults.total}</p>
            <p style="color: #10b981;"><strong>Passed:</strong> ${displayResults.passed} ${displayResults.total > 0 ? `(${((displayResults.passed/displayResults.total)*100).toFixed(1)}%)` : ''}</p>
            <p style="color: #ef4444;"><strong>Failed:</strong> ${displayResults.failed} ${displayResults.total > 0 ? `(${((displayResults.failed/displayResults.total)*100).toFixed(1)}%)` : ''}</p>
            <p style="color: #64748b;"><strong>Not Run:</strong> ${displayResults.notRun} ${displayResults.total > 0 ? `(${((displayResults.notRun/displayResults.total)*100).toFixed(1)}%)` : ''}</p>
            <hr style="margin: 15px 0; border: none; border-top: 1px solid #ddd;">
            <h4>Command Details:</h4>
            <div style="max-height: 400px; overflow-y: auto; margin-top: 10px;">
    `;
    
    displayResults.details.forEach(detail => {
        const statusColor = detail.status === 'PASSED' ? '#10b981' : detail.status === 'FAILED' ? '#ef4444' : '#64748b';
        const portInfo = detail.port ? ` [Port ${detail.port}]` : '';
        detailsHTML += `
            <div style="padding: 8px; margin: 5px 0; background: white; border-left: 3px solid ${statusColor}; border-radius: 4px;">
                <strong>${detail.command}${portInfo}</strong>
                <span style="float: right; color: ${statusColor};">${detail.status}</span>
                <br>
                <small style="color: #64748b;">${detail.message}</small>
            </div>
        `;
    });
    
    detailsHTML += '</div></div>';
    outputArea.innerHTML = detailsHTML;
}

// Save summary to file
function saveSummary() {
    if (testResults.total === 0) {
        alert('No test results available. Run commands first.');
        return;
    }
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    
    let summary = '='.repeat(70) + '\n';
    summary += 'UCSI DECODER - TEST RESULTS SUMMARY\n';
    summary += '='.repeat(70) + '\n\n';
    summary += `Date: ${new Date().toLocaleString()}\n`;
    summary += `Port: ${selectedPort}\n\n`;
    summary += `Total Commands: ${testResults.total}\n`;
    summary += `Passed: ${testResults.passed} (${((testResults.passed/testResults.total)*100).toFixed(1)}%)\n`;
    summary += `Failed: ${testResults.failed} (${((testResults.failed/testResults.total)*100).toFixed(1)}%)\n`;
    summary += `Not Run: ${testResults.notRun} (${((testResults.notRun/testResults.total)*100).toFixed(1)}%)\n\n`;
    summary += '='.repeat(70) + '\n';
    summary += 'DETAILED RESULTS\n';
    summary += '='.repeat(70) + '\n\n';
    
    testResults.details.forEach((detail, index) => {
        const portInfo = detail.port ? ` [Port ${detail.port}]` : '';
        summary += `${index + 1}. ${detail.command}${portInfo}\n`;
        summary += `   Status: ${detail.status}\n`;
        summary += `   Message: ${detail.message}\n\n`;
    });
    
    downloadTextFile(summary, `ucsi_results_${timestamp}.txt`);
    alert('Summary saved successfully!');
}

// Save all results with full details in PDF format
function saveAllResultsDetailedPDF() {
    // Check if jsPDF is available
    if (typeof jspdf === 'undefined') {
        alert('PDF library not loaded. Please refresh the page and try again.');
        return;
    }

    if (allDecodedResults.length === 0) {
        alert('No detailed results available. Run commands first.');
        return;
    }

    const timestamp = new Date().toISOString().replace(/:/g, '-').split('.')[0];
    const filename = `UCSI_Detailed_Results_${timestamp}.pdf`;

    try {
        const { jsPDF } = jspdf;
        const doc = new jsPDF({
            orientation: 'portrait',
            unit: 'mm',
            format: 'a4'
        });

        let yPos = 15;
        const pageWidth = doc.internal.pageSize.getWidth();
        const pageHeight = doc.internal.pageSize.getHeight();
        const margin = 15;
        const maxWidth = pageWidth - (2 * margin);

        // ===== TITLE PAGE =====
        doc.setFontSize(20);
        doc.setFont(undefined, 'bold');
        doc.text('UCSI DECODER', pageWidth / 2, yPos, { align: 'center' });
        yPos += 8;
        doc.setFontSize(16);
        doc.text('COMPREHENSIVE TEST RESULTS', pageWidth / 2, yPos, { align: 'center' });
        yPos += 15;

        // Summary statistics box
        doc.setFontSize(12);
        doc.setFont(undefined, 'bold');
        doc.text('TEST SUMMARY', margin, yPos);
        yPos += 8;

        doc.setFontSize(10);
        doc.setFont(undefined, 'normal');
        doc.text(`Total Commands Executed: ${testResults.total}`, margin + 5, yPos);
        yPos += 6;
        doc.setTextColor(34, 197, 94); // Green
        doc.text(`Passed: ${testResults.passed} (${((testResults.passed/testResults.total)*100).toFixed(1)}%)`, margin + 5, yPos);
        yPos += 6;
        doc.setTextColor(239, 68, 68); // Red
        doc.text(`Failed: ${testResults.failed} (${((testResults.failed/testResults.total)*100).toFixed(1)}%)`, margin + 5, yPos);
        yPos += 6;
        doc.setTextColor(156, 163, 175); // Gray
        doc.text(`Not Run: ${testResults.notRun} (${((testResults.notRun/testResults.total)*100).toFixed(1)}%)`, margin + 5, yPos);
        doc.setTextColor(0, 0, 0); // Reset to black
        yPos += 8;

        doc.text(`Generated: ${new Date().toLocaleString()}`, margin + 5, yPos);
        yPos += 6;
        doc.text(`Port: ${selectedPort}`, margin + 5, yPos);
        yPos += 6;
        doc.text(`UCSI Version: ${ucsiVersionSelect ? ucsiVersionSelect.value : detectedVersion}`, margin + 5, yPos);
        yPos += 10;

        // Draw separator
        doc.setDrawColor(200, 200, 200);
        doc.line(margin, yPos, pageWidth - margin, yPos);
        yPos += 10;

        // ===== INITIALIZATION FLOW SUMMARY =====
        doc.setFontSize(14);
        doc.setFont(undefined, 'bold');
        doc.setTextColor(37, 99, 235); // Blue
        doc.text('INITIALIZATION FLOW SUMMARY', margin, yPos);
        doc.setTextColor(0, 0, 0);
        yPos += 8;

        const initSummary = generateInitializationSummary(allDecodedResults);
        doc.setFontSize(9);
        doc.setFont(undefined, 'normal');

        initSummary.steps.forEach((step, idx) => {
            if (yPos > pageHeight - 25) {
                doc.addPage();
                yPos = 15;
            }

            const statusSymbol = step.completed ? '✓' : '✗';
            const statusColor = step.completed ? [34, 197, 94] : [239, 68, 68];

            doc.setTextColor(...statusColor);
            doc.setFont(undefined, 'bold');
            doc.text(`${statusSymbol} Test ${idx + 1}:`, margin, yPos);

            doc.setTextColor(0, 0, 0);
            doc.setFont(undefined, 'normal');
            const stepText = doc.splitTextToSize(step.description, maxWidth - 20);
            doc.text(stepText, margin + 20, yPos);
            yPos += stepText.length * 4;

            if (step.note) {
                doc.setFont(undefined, 'italic');
                doc.setFontSize(8);
                const noteText = doc.splitTextToSize(`Note: ${step.note}`, maxWidth - 20);
                doc.text(noteText, margin + 20, yPos);
                yPos += noteText.length * 3.5;
                doc.setFontSize(9);
            }
            yPos += 2;
        });

        // Overall compliance
        yPos += 5;
        if (yPos > pageHeight - 30) {
            doc.addPage();
            yPos = 15;
        }
        doc.setFontSize(10);
        doc.setFont(undefined, 'bold');
        doc.text('Overall Compliance:', margin, yPos);
        yPos += 6;
        doc.setFontSize(9);
        doc.setFont(undefined, 'normal');
        const compliancePercent = Math.round((initSummary.completedRequired / initSummary.totalRequired) * 100);
        const complianceColor = compliancePercent >= 80 ? [34, 197, 94] : compliancePercent >= 50 ? [234, 179, 8] : [239, 68, 68];
        doc.setTextColor(...complianceColor);
        doc.setFont(undefined, 'bold');
        doc.text(`${compliancePercent}% (${initSummary.completedRequired}/${initSummary.totalRequired} required steps)`, margin + 5, yPos);
        doc.setTextColor(0, 0, 0);
        yPos += 10;

        // Draw separator
        doc.setDrawColor(200, 200, 200);
        doc.line(margin, yPos, pageWidth - margin, yPos);
        yPos += 10;

        // ===== DETAILED RESULTS FOR EACH COMMAND =====
        doc.addPage();
        yPos = 15;
        
        doc.setFontSize(14);
        doc.setFont(undefined, 'bold');
        doc.setTextColor(37, 99, 235); // Blue
        doc.text('DETAILED COMMAND RESULTS', margin, yPos);
        doc.setTextColor(0, 0, 0);
        yPos += 10;

        allDecodedResults.forEach((result, index) => {
            // Check if we need a new page
            if (yPos > pageHeight - 40) {
                doc.addPage();
                yPos = 15;
            }

            // Command header with box
            doc.setFillColor(240, 249, 255); // Light blue background
            doc.rect(margin, yPos - 5, maxWidth, 10, 'F');
            doc.setDrawColor(59, 130, 246);
            doc.rect(margin, yPos - 5, maxWidth, 10, 'S');

            doc.setFontSize(11);
            doc.setFont(undefined, 'bold');
            doc.setTextColor(30, 64, 175); // Dark blue
            doc.text(`Test ${index + 1}: ${result.command}`, margin + 2, yPos + 1);
            doc.setTextColor(0, 0, 0);
            yPos += 12;

            // Metadata
            doc.setFontSize(9);
            doc.setFont(undefined, 'normal');
            doc.text(`Port: ${result.port}  |  Timestamp: ${result.timestamp}`, margin + 2, yPos);
            yPos += 6;

            const decoded = result.decoded;

            // Status indicator
            if (decoded.ErrorIndicator !== undefined) {
                const hasError = decoded.ErrorIndicator !== 0;
                doc.setFont(undefined, 'bold');
                if (hasError) {
                    doc.setTextColor(239, 68, 68); // Red
                    doc.text('✗ ERROR', margin + 2, yPos);
                } else {
                    doc.setTextColor(34, 197, 94); // Green
                    doc.text('✓ SUCCESS', margin + 2, yPos);
                }
                doc.setTextColor(0, 0, 0);
                doc.setFont(undefined, 'normal');
                doc.text(`ErrorIndicator: ${decoded.ErrorIndicator}`, margin + 25, yPos);
                yPos += 6;
            }

            // Display key decoded fields (limit to prevent overflow)
            let fieldCount = 0;
            const maxFields = 15;
            
            for (const [key, value] of Object.entries(decoded)) {
                if (['command', 'timestamp', 'raw_len', 'raw_hex', 'fields', 'UCSI_CONTROL', 'UCSI_VERSION', 'UCSI_CCI', 'optional_info', 'status_override', 'workflow_comparison', 'connector_status_before', 'connector_status_after', 'error', 'warning'].includes(key)) {
                    continue;
                }

                if (fieldCount >= maxFields) {
                    doc.setFont(undefined, 'italic');
                    doc.text('... (additional fields truncated)', margin + 2, yPos);
                    yPos += 5;
                    break;
                }

                if (yPos > pageHeight - 15) {
                    doc.addPage();
                    yPos = 15;
                }

                doc.setFont(undefined, 'bold');
                const fieldLabel = `${formatFieldName(key)}:`;
                doc.text(fieldLabel, margin + 2, yPos);
                doc.setFont(undefined, 'normal');

                const valueStr = typeof value === 'object' ? JSON.stringify(value).substring(0, 100) : String(value).substring(0, 100);
                const valueLines = doc.splitTextToSize(valueStr, maxWidth - 45);
                
                doc.text(valueLines[0], margin + 45, yPos);
                yPos += 5;
                
                fieldCount++;
            }

            // Separator between commands
            yPos += 2;
            doc.setDrawColor(220, 220, 220);
            doc.line(margin, yPos, pageWidth - margin, yPos);
            yPos += 6;
        });

        // Save the PDF
        doc.save(filename);
        showNotification(`Detailed results saved: ${filename}`, 'success');

    } catch (error) {
        console.error('PDF generation error:', error);
        alert('Error generating PDF: ' + error.message);
    }
}

// ===== SEQUENTIAL TEST FUNCTIONALITY =====

// Global variable to store sequential test configuration
let sequentialTestConfig = [];

// Show sequential test configuration dialog
function showStressTestDialog() {
    // Get all available commands
    const commandItems = Array.from(document.querySelectorAll('.command-item'));
    
    if (commandItems.length === 0) {
        alert('No commands available');
        return;
    }
    
    dialogTitle.textContent = 'Sequential Test Configuration';
    
    // Build command list
    let commandOptions = '';
    commandItems.forEach((item) => {
        const cmdKey = item.dataset.cmdKey;
        const category = item.dataset.category;
        commandOptions += `<option value="${cmdKey}">${cmdKey} (${category})</option>`;
    });
    
    dialogContent.innerHTML = `
        <div style="padding: 20px; max-height: 70vh; overflow-y: auto;">
            <div style="background: #e0f2fe; padding: 12px; border-radius: 6px; margin-bottom: 20px; border-left: 3px solid #0ea5e9;">
                <strong>ℹ️ Sequential Test:</strong> Commands will execute in the order you define below. Each command can have its own iteration count.
            </div>
            
            <!-- Add Command Section -->
            <div style="margin-bottom: 20px; background: #f8fafc; padding: 15px; border-radius: 8px; border: 2px dashed #cbd5e1;">
                <h4 style="margin-bottom: 12px; color: #1e293b;">➕ Add Command to Sequence</h4>
                <div style="display: grid; grid-template-columns: 3fr 1fr auto; gap: 10px; margin-bottom: 10px;">
                    <div>
                        <label style="display: block; margin-bottom: 4px; font-weight: 600; font-size: 12px;">Command:</label>
                        <select id="seqCommandSelect" style="width: 100%; padding: 8px; border: 1px solid #cbd5e1; border-radius: 4px;">
                            <option value="">-- Select Command --</option>
                            ${commandOptions}
                        </select>
                    </div>
                    <div>
                        <label style="display: block; margin-bottom: 4px; font-weight: 600; font-size: 12px;">Iterations:</label>
                        <input type="number" id="seqIterations" min="1" max="1000" value="1" 
                               style="width: 100%; padding: 8px; border: 1px solid #cbd5e1; border-radius: 4px;">
                    </div>
                    <div style="display: flex; align-items: flex-end;">
                        <button onclick="addSequentialCommand()" class="btn btn-primary" style="padding: 8px 16px; white-space: nowrap;">
                            ➕ Add
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- Command Sequence List -->
            <div style="margin-bottom: 20px;">
                <h4 style="margin-bottom: 10px; color: #1e293b;">📋 Command Sequence (Execution Order)</h4>
                <div id="sequenceList" style="border: 1px solid #cbd5e1; border-radius: 6px; padding: 10px; background: white; min-height: 150px; max-height: 250px; overflow-y: auto;">
                    <div style="text-align: center; color: #94a3b8; padding: 40px 20px;">
                        No commands added yet. Use the form above to add commands.
                    </div>
                </div>
            </div>
            
            <!-- Port Selection -->
            <div style="margin-bottom: 20px;">
                <h4 style="margin-bottom: 10px; color: #1e293b;">🔌 Port Selection:</h4>
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <label style="display: flex; align-items: center; cursor: pointer; padding: 8px 12px; border: 2px solid #cbd5e1; border-radius: 6px; background: #f8f9fa;">
                        <input type="checkbox" name="seqPort" value="1" ${selectedPort === 1 ? 'checked' : ''} style="margin-right: 8px;">
                        <span>Port 1</span>
                    </label>
                    <label style="display: flex; align-items: center; cursor: pointer; padding: 8px 12px; border: 2px solid #cbd5e1; border-radius: 6px; background: #f8f9fa;">
                        <input type="checkbox" name="seqPort" value="2" ${selectedPort === 2 ? 'checked' : ''} style="margin-right: 8px;">
                        <span>Port 2</span>
                    </label>
                    <label style="display: flex; align-items: center; cursor: pointer; padding: 8px 12px; border: 2px solid #cbd5e1; border-radius: 6px; background: #f8f9fa;">
                        <input type="checkbox" name="seqPort" value="3" ${selectedPort === 3 ? 'checked' : ''} style="margin-right: 8px;">
                        <span>Port 3</span>
                    </label>
                    <label style="display: flex; align-items: center; cursor: pointer; padding: 8px 12px; border: 2px solid #cbd5e1; border-radius: 6px; background: #f8f9fa;">
                        <input type="checkbox" name="seqPort" value="4" ${selectedPort === 4 ? 'checked' : ''} style="margin-right: 8px;">
                        <span>Port 4</span>
                    </label>
                </div>
                <small style="color: #64748b;">The sequence will run on each selected port</small>
            </div>
            
            <div style="margin-bottom: 20px;">
                <h4 style="margin-bottom: 10px; color: #1e293b;">⏱️ Timing Settings:</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div>
                        <label style="display: block; margin-bottom: 4px; font-weight: 600; font-size: 12px;">Delay Between Commands (ms):</label>
                        <input type="number" id="seqCommandDelay" min="0" max="10000" value="500" 
                               style="width: 100%; padding: 8px; border: 1px solid #cbd5e1; border-radius: 4px;">
                        <small style="color: #64748b;">Wait time between each command</small>
                    </div>
                </div>
            </div>
            
            <div style="background: #fff3cd; padding: 12px; border-radius: 6px; border-left: 3px solid #ffc107;">
                <strong>💡 Tip:</strong> Use ⬆️ ⬇️ buttons to reorder commands. Results will be auto-saved to a file.
            </div>
        </div>
    `;
    
    setTimeout(() => {
    
    // Initialize empty sequence
    sequentialTestConfig = [];
    
    dialogCancel.style.display = 'inline-block';
    dialogOk.textContent = 'Start Sequential Test';
    dialogOverlay.style.display = 'flex';
    dialogOverlay.dataset.type = 'stress_test';
}, 0);
}

// Add command to sequential test
window.addSequentialCommand = function() {
    const selectEl = document.getElementById('seqCommandSelect');
    const iterationsEl = document.getElementById('seqIterations');
    
    const command = selectEl.value;
    const iterations = parseInt(iterationsEl.value);
    
    if (!command) {
        alert('Please select a command');
        return;
    }
    
    if (iterations < 1 || iterations > 1000) {
        alert('Iterations must be between 1 and 1000');
        return;
    }
    
    // Add to config
    sequentialTestConfig.push({
        command: command,
        iterations: iterations,
        order: sequentialTestConfig.length + 1
    });
    
    // Reset form
    selectEl.value = '';
    iterationsEl.value = 1;
    
    // Update display
    updateSequenceList();
};

// Update sequence list display
function updateSequenceList() {
    const listEl = document.getElementById('sequenceList');
    
    if (sequentialTestConfig.length === 0) {
        listEl.innerHTML = `
            <div style="text-align: center; color: #94a3b8; padding: 40px 20px;">
                No commands added yet. Use the form above to add commands.
            </div>
        `;
        return;
    }
    
    let html = '';
    sequentialTestConfig.forEach((item, index) => {
        html += `
            <div style="display: flex; align-items: center; padding: 10px; margin-bottom: 8px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px;">
                <div style="flex: 0 0 40px; font-weight: bold; font-size: 16px; color: #3b82f6;">
                    ${index + 1}.
                </div>
                <div style="flex: 1; padding: 0 10px;">
                    <div style="font-weight: 600; color: #1e293b;">${item.command}</div>
                    <div style="font-size: 12px; color: #64748b;">Iterations: ${item.iterations}</div>
                </div>
                <div style="display: flex; gap: 4px;">
                    ${index > 0 ? `<button onclick="moveSequenceItem(${index}, 'up')" class="btn btn-small" style="padding: 4px 8px;">⬆️</button>` : ''}
                    ${index < sequentialTestConfig.length - 1 ? `<button onclick="moveSequenceItem(${index}, 'down')" class="btn btn-small" style="padding: 4px 8px;">⬇️</button>` : ''}
                    <button onclick="removeSequenceItem(${index})" class="btn btn-small" style="padding: 4px 8px; background: #ef4444; border-color: #ef4444;">🗑️</button>
                </div>
            </div>
        `;
    });
    
    listEl.innerHTML = html;
}

// Move sequence item up or down
window.moveSequenceItem = function(index, direction) {
    if (direction === 'up' && index > 0) {
        [sequentialTestConfig[index], sequentialTestConfig[index - 1]] = 
        [sequentialTestConfig[index - 1], sequentialTestConfig[index]];
    } else if (direction === 'down' && index < sequentialTestConfig.length - 1) {
        [sequentialTestConfig[index], sequentialTestConfig[index + 1]] = 
        [sequentialTestConfig[index + 1], sequentialTestConfig[index]];
    }
    updateSequenceList();
};

// Remove sequence item
window.removeSequenceItem = function(index) {
    sequentialTestConfig.splice(index, 1);
    updateSequenceList();
};

// Execute stress test
async function executeStressTest(mode, value, delay, commands, ports) {
    const startTime = Date.now();
    let totalTests = 0;
    let successCount = 0;
    let failCount = 0;
    let allResults = [];
    
    // Calculate total number of test runs
    const totalCombinations = commands.length * ports.length;
    
    outputArea.innerHTML = `
        <div style="padding: 20px; background: #f8f9fa; border-left: 4px solid #0071c5;">
            <h3>🔄 Stress Test Running...</h3>
            <p><strong>Commands:</strong> ${commands.join(', ')}</p>
            <p><strong>Ports:</strong> ${ports.join(', ')}</p>
            <p><strong>Mode:</strong> ${mode === 'iterations' ? value + ' iterations' : value + ' seconds'} per command/port</p>
            <p><strong>Delay:</strong> ${delay}ms</p>
            <p><strong>Total Combinations:</strong> ${totalCombinations}</p>
            <hr style="margin: 15px 0; border: none; border-top: 1px solid #ddd;">
            <div id="stressProgress"></div>
        </div>
    `;
    
    const progressDiv = document.getElementById('stressProgress');
    
    // Run test for each command/port combination
    for (let cmdIndex = 0; cmdIndex < commands.length; cmdIndex++) {
        const command = commands[cmdIndex];
        
        for (let portIndex = 0; portIndex < ports.length; portIndex++) {
            const port = ports[portIndex];
            const currentCombo = cmdIndex * ports.length + portIndex + 1;
            
            progressDiv.innerHTML = `
                <p><strong>Combination ${currentCombo}/${totalCombinations}:</strong> ${command} on Port ${port}</p>
                <div id="comboProgress"></div>
            `;
            
            const comboProgressDiv = document.getElementById('comboProgress');
            let iteration = 0;
            let comboSuccess = 0;
            let comboFail = 0;
            
            // Run test based on mode
            if (mode === 'iterations') {
                for (let i = 0; i < value; i++) {
                    iteration = i + 1;
                    totalTests++;
                    comboProgressDiv.innerHTML = `<p style="margin-left: 20px;">Iteration ${iteration} of ${value}...</p>`;
                    
                    const result = await simulateCommandExecution(command, port);
                    
                    if (result.status === 'PASSED') {
                        successCount++;
                        comboSuccess++;
                    } else {
                        failCount++;
                        comboFail++;
                    }
                    
                    allResults.push({
                        command: command,
                        port: port,
                        iteration: iteration,
                        status: result.status,
                        timestamp: new Date().toISOString()
                    });
                    
                    if (delay > 0) {
                        await new Promise(resolve => setTimeout(resolve, delay));
                    }
                }
            } else {
                // Time-based mode
                const comboEndTime = Date.now() + (value * 1000);
                while (Date.now() < comboEndTime) {
                    iteration++;
                    totalTests++;
                    const remaining = Math.ceil((comboEndTime - Date.now()) / 1000);
                    comboProgressDiv.innerHTML = `<p style="margin-left: 20px;">Iteration ${iteration}... (${remaining}s remaining)</p>`;
                    
                    const result = await simulateCommandExecution(command, port);
                    
                    if (result.status === 'PASSED') {
                        successCount++;
                        comboSuccess++;
                    } else {
                        failCount++;
                        comboFail++;
                    }
                    
                    allResults.push({
                        command: command,
                        port: port,
                        iteration: iteration,
                        status: result.status,
                        timestamp: new Date().toISOString()
                    });
                    
                    if (delay > 0) {
                        await new Promise(resolve => setTimeout(resolve, delay));
                    }
                }
            }
            
            // Show summary for this combination
            comboProgressDiv.innerHTML = `
                <p style="margin-left: 20px; color: #059669;">
                    ✅ Completed: ${comboSuccess} passed, ${comboFail} failed (Total: ${iteration})
                </p>
            `;
            
            // Small delay before next combination
            await new Promise(resolve => setTimeout(resolve, 200));
        }
    }
    
    const totalTime = ((Date.now() - startTime) / 1000).toFixed(2);
    const avgTime = totalTests > 0 ? (totalTime / totalTests * 1000).toFixed(2) : '0.00';
    const successRate = totalTests > 0 ? ((successCount / totalTests) * 100).toFixed(1) : '0.0';
    
    // Display results
    outputArea.innerHTML = `
        <div style="padding: 20px; background: #f8f9fa; border-left: 4px solid #28a745;">
            <h3>✅ Stress Test Completed</h3>
            <p><strong>Commands Tested:</strong> ${commands.join(', ')}</p>
            <p><strong>Ports Tested:</strong> ${ports.join(', ')}</p>
            <p><strong>Combinations:</strong> ${totalCombinations} (${commands.length} commands × ${ports.length} ports)</p>
            <hr style="margin: 15px 0; border: none; border-top: 1px solid #ddd;">
            <h4>Overall Results:</h4>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 15px 0;">
                <div style="background: white; padding: 15px; border-radius: 6px; text-align: center;">
                    <div style="font-size: 2em; font-weight: bold; color: #2563eb;">${totalTests}</div>
                    <div style="color: #64748b;">Total Executions</div>
                </div>
                <div style="background: white; padding: 15px; border-radius: 6px; text-align: center;">
                    <div style="font-size: 2em; font-weight: bold; color: #10b981;">${successCount}</div>
                    <div style="color: #64748b;">Successful</div>
                </div>
                <div style="background: white; padding: 15px; border-radius: 6px; text-align: center;">
                    <div style="font-size: 2em; font-weight: bold; color: #ef4444;">${failCount}</div>
                    <div style="color: #64748b;">Failed</div>
                </div>
                <div style="background: white; padding: 15px; border-radius: 6px; text-align: center;">
                    <div style="font-size: 2em; font-weight: bold; color: #0071c5;">${successRate}%</div>
                    <div style="color: #64748b;">Success Rate</div>
                </div>
            </div>
            <p><strong>Total Time:</strong> ${totalTime} seconds</p>
            <p><strong>Average Time per Command:</strong> ${avgTime} ms</p>
            <hr style="margin: 15px 0; border: none; border-top: 1px solid #ddd;">
            <button onclick="downloadStressTestResults(${JSON.stringify(allResults).replace(/"/g, '&quot;')}, ${JSON.stringify(commands)}, ${JSON.stringify(ports)}, ${totalTests}, ${successCount}, ${failCount}, ${totalTime}, ${avgTime})" 
                    style="padding: 10px 20px; background: #2563eb; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600;">
                💾 Download Detailed Results
            </button>
        </div>
    `;
}

// Execute sequential test with custom ordering
async function executeSequentialTest(sequenceConfig, ports, commandDelay) {
    const startTime = Date.now();
    let totalTests = 0;
    let successCount = 0;
    let failCount = 0;
    let allResults = [];
    
    // Clear accumulated decoded results for fresh test
    allDecodedResults = [];
    
    // Calculate total number of test runs
    let totalIterations = 0;
    sequenceConfig.forEach(config => {
        totalIterations += config.iterations * ports.length;
    });
    
    outputArea.innerHTML = `
        <div style="padding: 20px; background: #f8f9fa; border-left: 4px solid #0071c5;">
            <h3>🔄 Sequential Test Running...</h3>
            <p><strong>Commands in sequence:</strong> ${sequenceConfig.length}</p>
            <p><strong>Ports:</strong> ${ports.join(', ')}</p>
            <p><strong>Total iterations:</strong> ${totalIterations}</p>
            <p><strong>Command delay:</strong> ${commandDelay}ms</p>
            <hr style="margin: 15px 0; border: none; border-top: 1px solid #ddd;">
            <div id="seqProgress"></div>
        </div>
    `;
    
    const progressDiv = document.getElementById('seqProgress');
    
    // Execute commands in sequence
    for (let seqIndex = 0; seqIndex < sequenceConfig.length; seqIndex++) {
        const config = sequenceConfig[seqIndex];
        const command = config.command;
        const iterations = config.iterations;
        
        progressDiv.innerHTML = `
            <p><strong>Step ${seqIndex + 1}/${sequenceConfig.length}:</strong> ${command} (${iterations} iterations per port)</p>
            <div id="stepProgress"></div>
        `;
        
        const stepProgressDiv = document.getElementById('stepProgress');
        
        // Execute on each port
        for (let portIndex = 0; portIndex < ports.length; portIndex++) {
            const port = ports[portIndex];
            
            stepProgressDiv.innerHTML = `
                <p style="margin-left: 20px;"><strong>Port ${port}:</strong> Running ${iterations} iterations...</p>
                <div id="portProgress"></div>
            `;
            
            const portProgressDiv = document.getElementById('portProgress');
            let portSuccess = 0;
            let portFail = 0;
            
            // Run iterations for this command/port
            for (let iter = 0; iter < iterations; iter++) {
                totalTests++;
                portProgressDiv.innerHTML = `<p style="margin-left: 40px;">Iteration ${iter + 1} of ${iterations}...</p>`;
                
                // Execute command
                const result = await simulateCommandExecution(command, port);
                
                if (result.status === 'PASSED') {
                    successCount++;
                    portSuccess++;
                } else {
                    failCount++;
                    portFail++;
                }
                
                allResults.push({
                    sequenceStep: seqIndex + 1,
                    command: command,
                    port: port,
                    iteration: iter + 1,
                    status: result.status,
                    timestamp: new Date().toISOString()
                });
                
                // Delay between commands
                if (commandDelay > 0) {
                    await new Promise(resolve => setTimeout(resolve, commandDelay));
                }
            }
            
            // Show port summary
            portProgressDiv.innerHTML = `
                <p style="margin-left: 40px; color: #059669;">
                    ✅ Port ${port} completed: ${portSuccess} passed, ${portFail} failed
                </p>
            `;
            
            await new Promise(resolve => setTimeout(resolve, 200));
        }
        
        // Show step summary
        stepProgressDiv.innerHTML += `
            <p style="margin-left: 20px; color: #059669;">
                ✅ Step ${seqIndex + 1} completed
            </p>
        `;
        
        await new Promise(resolve => setTimeout(resolve, 300));
    }
    
    const totalTime = ((Date.now() - startTime) / 1000).toFixed(2);
    const avgTime = totalTests > 0 ? (totalTime / totalTests * 1000).toFixed(2) : '0.00';
    const successRate = totalTests > 0 ? ((successCount / totalTests) * 100).toFixed(1) : '0.0';
    
    // Display results
    outputArea.innerHTML = `
        <div style="padding: 20px; background: #f8f9fa; border-left: 4px solid #28a745;">
            <h3>✅ Sequential Test Completed</h3>
            <p><strong>Sequence:</strong> ${sequenceConfig.map((c, i) => `${i+1}. ${c.command} (${c.iterations}×)`).join(', ')}</p>
            <p><strong>Ports Tested:</strong> ${ports.join(', ')}</p>
            <hr style="margin: 15px 0; border: none; border-top: 1px solid #ddd;">
            <h4>Overall Results:</h4>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 15px 0;">
                <div style="background: white; padding: 15px; border-radius: 6px; text-align: center;">
                    <div style="font-size: 2em; font-weight: bold; color: #2563eb;">${totalTests}</div>
                    <div style="color: #64748b;">Total Executions</div>
                </div>
                <div style="background: white; padding: 15px; border-radius: 6px; text-align: center;">
                    <div style="font-size: 2em; font-weight: bold; color: #10b981;">${successCount}</div>
                    <div style="color: #64748b;">Successful</div>
                </div>
                <div style="background: white; padding: 15px; border-radius: 6px; text-align: center;">
                    <div style="font-size: 2em; font-weight: bold; color: #ef4444;">${failCount}</div>
                    <div style="color: #64748b;">Failed</div>
                </div>
                <div style="background: white; padding: 15px; border-radius: 6px; text-align: center;">
                    <div style="font-size: 2em; font-weight: bold; color: #0071c5;">${successRate}%</div>
                    <div style="color: #64748b;">Success Rate</div>
                </div>
            </div>
            <p><strong>Total Time:</strong> ${totalTime} seconds</p>
            <p><strong>Average Time per Command:</strong> ${avgTime} ms</p>
            <hr style="margin: 15px 0; border: none; border-top: 1px solid #ddd;">
            <div id="autoSaveStatus" style="padding: 10px; background: #fff3cd; border-radius: 6px; margin-bottom: 10px;">
                <strong>💾 Auto-saving results...</strong>
            </div>
        </div>
    `;
    
    // Auto-save results to file
    await autoSaveSequentialResults(sequenceConfig, ports, allResults, totalTests, successCount, failCount, totalTime, avgTime);
    
    // Show Save All Results PDF button if we have detailed results
    if (saveAllResultsPDFBtn && allDecodedResults.length > 0) {
        saveAllResultsPDFBtn.style.display = 'inline-block';
    }
}

// Auto-save sequential test results to file
async function autoSaveSequentialResults(sequenceConfig, ports, results, total, success, fail, totalTime, avgTime) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    const filename = `Sequential_Test_${timestamp}.txt`;
    
    let report = '='.repeat(70) + '\n';
    report += 'UCSI DECODER - SEQUENTIAL TEST RESULTS\n';
    report += '='.repeat(70) + '\n\n';
    report += `Date: ${new Date().toLocaleString()}\n`;
    report += `Test Type: Sequential (Custom Ordered)\n\n`;
    
    report += 'COMMAND SEQUENCE:\n';
    sequenceConfig.forEach((config, index) => {
        report += `  ${index + 1}. ${config.command} - ${config.iterations} iterations\n`;
    });
    
    report += `\nPorts: ${ports.join(', ')}\n`;
    report += '\n';
    
    report += `Total Executions: ${total}\n`;
    report += `Successful: ${success}\n`;
    report += `Failed: ${fail}\n`;
    report += `Success Rate: ${((success / total) * 100).toFixed(1)}%\n`;
    report += `Total Time: ${totalTime} seconds\n`;
    report += `Average Time per Command: ${avgTime} ms\n\n`;
    
    report += '='.repeat(70) + '\n';
    report += 'DETAILED RESULTS\n';
    report += '='.repeat(70) + '\n\n';
    
    let currentStep = 0;
    let currentPort = -1;
    results.forEach((result, index) => {
        if (result.sequenceStep !== currentStep) {
            currentStep = result.sequenceStep;
            report += `\n--- STEP ${currentStep}: ${result.command} ---\n`;
        }
        if (result.port !== currentPort) {
            currentPort = result.port;
            report += `\nPort ${currentPort}:\n`;
        }
        report += `  [${result.timestamp}] Iteration ${result.iteration}: ${result.status}\n`;
    });
    
    report += '\n' + '='.repeat(70) + '\n';
    report += 'END OF REPORT\n';
    report += '='.repeat(70) + '\n';
    
    try {
        const response = await fetch('/save_test_results', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                filename: filename,
                content: report
            })
        });
        
        const data = await response.json();
        const statusDiv = document.getElementById('autoSaveStatus');
        
        if (data.success) {
            statusDiv.innerHTML = `
                <strong style="color: #059669;">✅ Results auto-saved successfully!</strong><br>
                <span style="font-size: 0.9em;">File: ${data.filepath}</span>
            `;
            statusDiv.style.background = '#d1fae5';
        } else {
            statusDiv.innerHTML = `
                <strong style="color: #dc2626;">❌ Failed to auto-save results</strong><br>
                <span style="font-size: 0.9em;">Error: ${data.error}</span>
            `;
            statusDiv.style.background = '#fee2e2';
        }
    } catch (error) {
        const statusDiv = document.getElementById('autoSaveStatus');
        statusDiv.innerHTML = `
            <strong style="color: #dc2626;">❌ Failed to auto-save results</strong><br>
            <span style="font-size: 0.9em;">Error: ${error.message}</span>
        `;
        statusDiv.style.background = '#fee2e2';
    }
}

// Download stress test results - globally accessible
window.downloadStressTestResults = function(results, commands, ports, total, success, fail, totalTime, avgTime) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    
    let report = '='.repeat(70) + '\n';
    report += 'UCSI DECODER - STRESS TEST RESULTS\n';
    report += '='.repeat(70) + '\n\n';
    report += `Date: ${new Date().toLocaleString()}\n`;
    report += `Commands: ${commands.join(', ')}\n`;
    report += `Ports: ${ports.join(', ')}\n`;
    report += `Combinations: ${commands.length} commands × ${ports.length} ports = ${commands.length * ports.length}\n\n`;
    report += `Total Executions: ${total}\n`;
    report += `Successful: ${success}\n`;
    report += `Failed: ${fail}\n`;
    report += `Success Rate: ${((success/total)*100).toFixed(1)}%\n`;
    report += `Total Time: ${totalTime} seconds\n`;
    report += `Average Time per Command: ${avgTime} ms\n\n`;
    report += '='.repeat(70) + '\n';
    report += 'DETAILED RESULTS\n';
    report += '='.repeat(70) + '\n\n';
    
    results.forEach((result, index) => {
        report += `Test ${index + 1}:\n`;
        report += `  Command: ${result.command}\n`;
        report += `  Port: ${result.port}\n`;
        report += `  Iteration: ${result.iteration}\n`;
        report += `  Status: ${result.status}\n`;
        report += `  Timestamp: ${result.timestamp}\n\n`;
    });
    
    downloadTextFile(report, `stress_test_${timestamp}.txt`);
    alert('Stress test results downloaded successfully!');
};

// ==============================================
// Concurrent Test Dialog
// ==============================================

// Show concurrent test configuration dialog (similar to stress test but runs in parallel)
function showConcurrentTestDialog() {
    // Get all available commands
    const commandItems = Array.from(document.querySelectorAll('.command-item'));
    
    if (commandItems.length === 0) {
        alert('No commands available');
        return;
    }
    
    dialogTitle.textContent = 'Concurrent Test Configuration (2 Threads)';
    
    // Build command options for dropdowns
    let commandOptions = '<option value="">-- Select Command --</option>';
    commandItems.forEach((item) => {
        const cmdKey = item.dataset.cmdKey;
        const category = item.dataset.category;
        commandOptions += `<option value="${cmdKey}">${cmdKey} (${category})</option>`;
    });
    
    dialogContent.innerHTML = `
        <div style="padding: 20px; max-height: 70vh; overflow-y: auto;">
            <p style="margin-bottom: 20px; padding: 12px; background: #dbeafe; border-left: 4px solid #2563eb; border-radius: 4px; font-size: 13px;">
                <strong>⚡ Concurrent Testing:</strong> Configure two independent threads that run simultaneously.
                Both threads run UCSI commands on independent ports at the same time.
            </p>
            
            <!-- Thread 1 Configuration -->
            <div style="margin-bottom: 25px; padding: 15px; border: 2px solid #3b82f6; border-radius: 8px; background: #eff6ff;">
                <h4 style="margin: 0 0 15px 0; color: #1e40af; display: flex; align-items: center;">
                    <span style="background: #3b82f6; color: white; padding: 4px 10px; border-radius: 4px; margin-right: 10px; font-size: 12px;">THREAD 1</span>
                    Configuration
                </h4>
                
                <div style="margin-bottom: 12px;">
                    <label style="display: block; margin-bottom: 6px; font-weight: 600; font-size: 13px;">Operation Type:</label>
                    <select id="thread1Type" onchange="updateThread1Options()" style="width: 100%; padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px;">
                        <option value="command">⚙️ Run Command</option>
                    </select>
                </div>
                
                <div id="thread1CommandOptions">
                    <div style="margin-bottom: 12px;">
                        <label style="display: block; margin-bottom: 6px; font-weight: 600; font-size: 13px;">Command:</label>
                        <select id="thread1Command" style="width: 100%; padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px;">
                            ${commandOptions}
                        </select>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px;">
                    <div>
                        <label style="display: block; margin-bottom: 6px; font-weight: 600; font-size: 13px;">UCSI Port:</label>
                        <select id="thread1Port" style="width: 100%; padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px;">
                            <option value="0">Port 0</option>
                            <option value="1">Port 1</option>
                            <option value="2">Port 2</option>
                            <option value="3">Port 3</option>
                        </select>
                    </div>
                    <div>
                        <label style="display: block; margin-bottom: 6px; font-weight: 600; font-size: 13px;">Iterations:</label>
                        <input type="number" id="thread1Iterations" value="5" min="1" max="100" 
                               style="width: 100%; padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px;">
                    </div>
                    <div>
                        <label style="display: block; margin-bottom: 6px; font-weight: 600; font-size: 13px;">Delay (ms):</label>
                        <input type="number" id="thread1Delay" value="1000" min="0" max="10000" step="100"
                               style="width: 100%; padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px;">
                    </div>
                </div>
            </div>
            
            <!-- Thread 2 Configuration -->
            <div style="margin-bottom: 25px; padding: 15px; border: 2px solid #10b981; border-radius: 8px; background: #ecfdf5;">
                <h4 style="margin: 0 0 15px 0; color: #047857; display: flex; align-items: center;">
                    <span style="background: #10b981; color: white; padding: 4px 10px; border-radius: 4px; margin-right: 10px; font-size: 12px;">THREAD 2</span>
                    Configuration
                </h4>
                
                <div style="margin-bottom: 12px;">
                    <label style="display: block; margin-bottom: 6px; font-weight: 600; font-size: 13px;">Operation Type:</label>
                    <select id="thread2Type" onchange="updateThread2Options()" style="width: 100%; padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px;">
                        <option value="command">⚙️ Run Command</option>
                    </select>
                </div>
                
                <div id="thread2CommandOptions">
                    <div style="margin-bottom: 12px;">
                        <label style="display: block; margin-bottom: 6px; font-weight: 600; font-size: 13px;">Command:</label>
                        <select id="thread2Command" style="width: 100%; padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px;">
                            ${commandOptions}
                        </select>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px;">
                        </select>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px;">
                    <div>
                        <label style="display: block; margin-bottom: 6px; font-weight: 600; font-size: 13px;">UCSI Port:</label>
                        <select id="thread2Port" style="width: 100%; padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px;">
                            <option value="0">Port 0</option>
                            <option value="1">Port 1</option>
                            <option value="2">Port 2</option>
                            <option value="3">Port 3</option>
                        </select>
                    </div>
                    <div>
                        <label style="display: block; margin-bottom: 6px; font-weight: 600; font-size: 13px;">Iterations:</label>
                        <input type="number" id="thread2Iterations" value="5" min="1" max="100" 
                               style="width: 100%; padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px;">
                    </div>
                    <div>
                        <label style="display: block; margin-bottom: 6px; font-weight: 600; font-size: 13px;">Delay (ms):</label>
                        <input type="number" id="thread2Delay" value="1000" min="0" max="10000" step="100"
                               style="width: 100%; padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px;">
                    </div>
                </div>
            </div>
            
            <!-- Synchronization Options -->
            <div style="margin-bottom: 20px; padding: 15px; border: 2px solid #8b5cf6; border-radius: 8px; background: #f5f3ff;">
                <h4 style="margin: 0 0 15px 0; color: #6b21a8;">⏱️ Synchronization</h4>
                
                <div style="margin-bottom: 12px;">
                    <label style="display: block; margin-bottom: 6px; font-weight: 600; font-size: 13px;">Execution Mode:</label>
                    <select id="syncMode" onchange="updateSyncOptions()" style="width: 100%; padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px;">
                        <option value="simultaneous">⚡ Simultaneous (both start at same time)</option>
                        <option value="offset">⏱️ Offset (Thread 2 starts after delay)</option>
                        <option value="interleaved">🔄 Interleaved (alternate iterations)</option>
                    </select>
                </div>
                
                <div id="offsetOptions" style="display: none; margin-bottom: 12px;">
                    <label style="display: block; margin-bottom: 6px; font-weight: 600; font-size: 13px;">Thread 2 Start Delay (ms):</label>
                    <input type="number" id="thread2StartDelay" value="500" min="0" max="10000" step="100"
                           style="width: 150px; padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px;">
                    <small style="color: #64748b; margin-left: 10px;">Delay before Thread 2 starts</small>
                </div>
            </div>
        </div>
    `;
    
    dialogCancel.style.display = 'inline-block';
    dialogOk.textContent = 'Start Concurrent Test';
    dialogOverlay.style.display = 'flex';
    dialogOverlay.dataset.type = 'concurrent_test';
}

// Update Thread 1 options based on operation type
window.updateThread1Options = function() {
    // Only command type supported
}

// Update Thread 2 options based on operation type
window.updateThread2Options = function() {
    // Only command type supported
}

// Update sync options based on mode
window.updateSyncOptions = function() {
    const mode = document.getElementById('syncMode').value;
    const offsetOptions = document.getElementById('offsetOptions');
    offsetOptions.style.display = (mode === 'offset') ? 'block' : 'none';
}

// Execute concurrent test (runs commands in parallel)
async function executeConcurrentTest(iterations, delay, commands, ports) {
    const startTime = Date.now();
    let allResults = [];
    
    // Clear accumulated decoded results for fresh test
    allDecodedResults = [];
    
    outputArea.innerHTML = `
        <div style="padding: 20px; background: #f8f9fa; border-left: 4px solid #8b5cf6;">
            <h3>⚡ Concurrent Test Running...</h3>
            <p><strong>Commands:</strong> ${commands.join(', ')}</p>
            <p><strong>Ports:</strong> ${ports.join(', ')}</p>
            <p><strong>Iterations:</strong> ${iterations}</p>
            <p><strong>Delay:</strong> ${delay}ms between batches</p>
            <p><strong>Execution:</strong> All combinations run simultaneously</p>
            <hr style="margin: 15px 0; border: none; border-top: 1px solid #ddd;">
            <div id="concurrentProgress"></div>
        </div>
    `;
    
    const progressDiv = document.getElementById('concurrentProgress');
    
    // Run iterations
    for (let iter = 1; iter <= iterations; iter++) {
        progressDiv.innerHTML = `<p><strong>Batch ${iter}/${iterations}:</strong> Running all combinations concurrently...</p>`;
        
        // Create array of all command/port combinations to run in parallel
        const promises = [];
        
        for (const command of commands) {
            for (const port of ports) {
                // Create promise for this command/port combination
                const promise = (async () => {
                    try {
                        const result = await executeCommand(command, parseInt(port));
                        return {
                            command: command,
                            port: port,
                            iteration: iter,
                            status: result.success ? 'PASS' : 'FAIL',
                            message: result.message || '',
                            timestamp: new Date().toISOString()
                        };
                    } catch (error) {
                        return {
                            command: command,
                            port: port,
                            iteration: iter,
                            status: 'ERROR',
                            message: error.message,
                            timestamp: new Date().toISOString()
                        };
                    }
                })();
                
                promises.push(promise);
            }
        }
        
        // Wait for all commands in this batch to complete
        const batchResults = await Promise.all(promises);
        allResults.push(...batchResults);
        
        // Delay before next batch (except last iteration)
        if (iter < iterations && delay > 0) {
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }
    
    const endTime = Date.now();
    const totalTime = ((endTime - startTime) / 1000).toFixed(2);
    const avgTime = ((endTime - startTime) / allResults.length).toFixed(0);
    
    // Calculate statistics
    const success = allResults.filter(r => r.status === 'PASS').length;
    const fail = allResults.filter(r => r.status !== 'PASS').length;
    const total = allResults.length;
    
    // Display results
    outputArea.innerHTML = `
        <div style="padding: 20px; background: #f8f9fa; border-left: 4px solid #8b5cf6;">
            <h3>⚡ Concurrent Test Complete</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin: 15px 0;">
                <div style="padding: 10px; background: white; border-radius: 6px; text-align: center;">
                    <div style="font-size: 24px; color: #10b981; font-weight: bold;">${success}</div>
                    <div style="font-size: 12px; color: #64748b;">PASSED</div>
                </div>
                <div style="padding: 10px; background: white; border-radius: 6px; text-align: center;">
                    <div style="font-size: 24px; color: #ef4444; font-weight: bold;">${fail}</div>
                    <div style="font-size: 12px; color: #64748b;">FAILED</div>
                </div>
                <div style="padding: 10px; background: white; border-radius: 6px; text-align: center;">
                    <div style="font-size: 24px; color: #3b82f6; font-weight: bold;">${total}</div>
                    <div style="font-size: 12px; color: #64748b;">TOTAL</div>
                </div>
                <div style="padding: 10px; background: white; border-radius: 6px; text-align: center;">
                    <div style="font-size: 24px; color: #f59e0b; font-weight: bold;">${totalTime}s</div>
                    <div style="font-size: 12px; color: #64748b;">DURATION</div>
                </div>
            </div>
            <div style="margin-top: 15px;">
                <button onclick="downloadConcurrentReport()" class="btn btn-primary">📥 Download Report</button>
            </div>
        </div>
    `;
    
    // Store results for download
    window.lastConcurrentResults = allResults;
    window.lastConcurrentStats = { total, success, fail, totalTime, avgTime, commands, ports, iterations };
}

// Download concurrent test report
window.downloadConcurrentReport = function() {
    const results = window.lastConcurrentResults || [];
    const stats = window.lastConcurrentStats || {};
    
    if (results.length === 0) {
        alert('No concurrent test results available');
        return;
    }
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    
    let report = '='.repeat(70) + '\n';
    report += 'CONCURRENT TEST REPORT\n';
    report += '='.repeat(70) + '\n\n';
    report += `Test Type: Concurrent (Parallel Execution)\n`;
    report += `Timestamp: ${new Date().toLocaleString()}\n\n`;
    report += `Commands: ${stats.commands.join(', ')}\n`;
    report += `Ports: ${stats.ports.join(', ')}\n`;
    report += `Iterations: ${stats.iterations}\n`;
    report += `Combinations per Batch: ${stats.commands.length} commands × ${stats.ports.length} ports = ${stats.commands.length * stats.ports.length}\n\n`;
    report += `Total Executions: ${stats.total}\n`;
    report += `Successful: ${stats.success}\n`;
    report += `Failed: ${stats.fail}\n`;
    report += `Success Rate: ${((stats.success/stats.total)*100).toFixed(1)}%\n`;
    report += `Total Time: ${stats.totalTime} seconds\n`;
    report += `Average Time per Command: ${stats.avgTime} ms\n\n`;
    report += '='.repeat(70) + '\n';
    report += 'DETAILED RESULTS\n';
    report += '='.repeat(70) + '\n\n';
    
    results.forEach((result, index) => {
        report += `Test ${index + 1}:\n`;
        report += `  Command: ${result.command}\n`;
        report += `  Port: ${result.port}\n`;
        report += `  Iteration: ${result.iteration}\n`;
        report += `  Status: ${result.status}\n`;
        report += `  Timestamp: ${result.timestamp}\n\n`;
    });
    
    downloadTextFile(report, `concurrent_test_${timestamp}.txt`);
    alert('Concurrent test results downloaded successfully!');
};

// ==============================================
// Concurrent Test V2 (2-Thread)
// ==============================================

async function executeConcurrentTestV2(thread1Config, thread2Config, syncMode, thread2StartDelay) {
    const startTime = Date.now();
    let thread1Results = [];
    let thread2Results = [];
    let combinedLogs = [];
    
    // Clear accumulated decoded results for fresh test
    allDecodedResults = [];
    
    // Initialize output area
    outputArea.innerHTML = `
        <div style="padding: 20px; background: #f8f9fa; border-left: 4px solid #8b5cf6;">
            <h3>⚡ Concurrent Test Running (2 Threads)</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 15px;">
                <div style="padding: 12px; background: #eff6ff; border-left: 3px solid #3b82f6; border-radius: 4px;">
                    <strong style="color: #1e40af;">🔵 Thread 1:</strong> ${getThreadDescription(thread1Config)}<br>
                    <small>Iterations: ${thread1Config.iterations}, Delay: ${thread1Config.delay}ms</small>
                </div>
                <div style="padding: 12px; background: #ecfdf5; border-left: 3px solid #10b981; border-radius: 4px;">
                    <strong style="color: #047857;">🟢 Thread 2:</strong> ${getThreadDescription(thread2Config)}<br>
                    <small>Iterations: ${thread2Config.iterations}, Delay: ${thread2Config.delay}ms</small>
                </div>
            </div>
            <p style="margin-top: 15px;"><strong>Sync Mode:</strong> ${getSyncModeDescription(syncMode, thread2StartDelay)}</p>
            <hr style="margin: 15px 0; border: none; border-top: 1px solid #ddd;">
            <div id="concurrentLogs" style="background: #1e293b; color: #f1f5f9; padding: 15px; border-radius: 6px; max-height: 400px; overflow-y: auto; font-family: 'Courier New', monospace; font-size: 12px;">
                <div style="color: #94a3b8;">Starting concurrent test...</div>
            </div>
        </div>
    `;
    
    const logsDiv = document.getElementById('concurrentLogs');
    
    // Helper function to add log entry
    function addLog(threadName, color, message) {
        const timestamp = new Date().toISOString().split('T')[1].slice(0, -1);
        const logEntry = `<div style="margin: 2px 0;"><span style="color: #64748b;">[${timestamp}]</span> <span style="color: ${color}; font-weight: bold;">${threadName}:</span> ${message}</div>`;
        logsDiv.innerHTML += logEntry;
        logsDiv.scrollTop = logsDiv.scrollHeight;
        
        combinedLogs.push({
            timestamp: new Date().toISOString(),
            thread: threadName,
            message: message
        });
    }
    
    // Thread execution functions
    async function executeThread(threadConfig, threadName, color) {
        const results = [];
        addLog(threadName, color, `Started (${threadConfig.iterations} iterations)`);
        
        for (let i = 1; i <= threadConfig.iterations; i++) {
            addLog(threadName, color, `Iteration ${i}/${threadConfig.iterations}`);
            
            if (threadConfig.type === 'command') {
                // Execute UCSI command
                addLog(threadName, color, `Running ${threadConfig.command} on Port ${threadConfig.port}...`);
                try {
                    const result = await executeCommand(threadConfig.command, threadConfig.port);
                    const status = result.success ? 'PASS' : 'FAIL';
                    addLog(threadName, color, `✓ ${threadConfig.command} - ${status}`);
                    
                    results.push({
                        iteration: i,
                        type: 'command',
                        command: threadConfig.command,
                        port: threadConfig.port,
                        status: status,
                        timestamp: new Date().toISOString()
                    });
                } catch (error) {
                    addLog(threadName, color, `✗ Error: ${error.message}`);
                    results.push({
                        iteration: i,
                        type: 'command',
                        command: threadConfig.command,
                        port: threadConfig.port,
                        status: 'ERROR',
                        error: error.message,
                        timestamp: new Date().toISOString()
                    });
                }
            }
            
            // Delay between iterations (except last)
            if (i < threadConfig.iterations && threadConfig.delay > 0) {
                await new Promise(resolve => setTimeout(resolve, threadConfig.delay));
            }
        }
        
        addLog(threadName, color, `Completed all ${threadConfig.iterations} iterations`);
        return results;
    }
    
    // Execute based on sync mode
    if (syncMode === 'simultaneous') {
        // Both threads start at same time
        addLog('SYSTEM', '#f59e0b', 'Starting both threads simultaneously...');
        const [t1Results, t2Results] = await Promise.all([
            executeThread(thread1Config, 'Thread 1', '#3b82f6'),
            executeThread(thread2Config, 'Thread 2', '#10b981')
        ]);
        thread1Results = t1Results;
        thread2Results = t2Results;
        
    } else if (syncMode === 'offset') {
        // Thread 2 starts after delay
        addLog('SYSTEM', '#f59e0b', 'Starting Thread 1...');
        const thread1Promise = executeThread(thread1Config, 'Thread 1', '#3b82f6');
        
        addLog('SYSTEM', '#f59e0b', `Waiting ${thread2StartDelay}ms before starting Thread 2...`);
        await new Promise(resolve => setTimeout(resolve, thread2StartDelay));
        
        addLog('SYSTEM', '#f59e0b', 'Starting Thread 2...');
        const thread2Promise = executeThread(thread2Config, 'Thread 2', '#10b981');
        
        [thread1Results, thread2Results] = await Promise.all([thread1Promise, thread2Promise]);
        
    } else if (syncMode === 'interleaved') {
        // Alternate iterations between threads
        addLog('SYSTEM', '#f59e0b', 'Starting interleaved execution...');
        const maxIterations = Math.max(thread1Config.iterations, thread2Config.iterations);
        
        for (let i = 1; i <= maxIterations; i++) {
            if (i <= thread1Config.iterations) {
                addLog('Thread 1', '#3b82f6', `Iteration ${i}/${thread1Config.iterations}`);
                const result = await executeSingleIteration(thread1Config, i, 'Thread 1', '#3b82f6');
                thread1Results.push(result);
            }
            
            if (i <= thread2Config.iterations) {
                addLog('Thread 2', '#10b981', `Iteration ${i}/${thread2Config.iterations}`);
                const result = await executeSingleIteration(thread2Config, i, 'Thread 2', '#10b981');
                thread2Results.push(result);
            }
        }
    }
    
    const endTime = Date.now();
    const totalTime = ((endTime - startTime) / 1000).toFixed(2);
    
    addLog('SYSTEM', '#f59e0b', `✅ Test completed in ${totalTime} seconds`);
    
    // Display results summary
    showConcurrentTestResults(thread1Config, thread2Config, thread1Results, thread2Results, combinedLogs, totalTime, syncMode);
}

// Helper function for single iteration (interleaved mode)
async function executeSingleIteration(config, iteration, threadName, color) {
    const result = { iteration: iteration, timestamp: new Date().toISOString() };
    
    if (config.type === 'command') {
        try {
            const cmdResult = await executeCommand(config.command, config.port);
            result.type = 'command';
            result.command = config.command;
            result.port = config.port;
            result.status = cmdResult.success ? 'PASS' : 'FAIL';
        } catch (error) {
            result.type = 'command';
            result.command = config.command;
            result.port = config.port;
            result.status = 'ERROR';
            result.error = error.message;
        }
    }
    // Add other operation types as needed...
    
    if (config.delay > 0) {
        await new Promise(resolve => setTimeout(resolve, config.delay));
    }
    
    return result;
}

// Helper function to get thread description
function getThreadDescription(config) {
    if (config.type === 'command') {
        return `${config.command} on Port ${config.port}`;
    }
    return 'Unknown';
}

// Helper function to get sync mode description
function getSyncModeDescription(mode, delay) {
    if (mode === 'simultaneous') {
        return '⚡ Simultaneous (both threads start at same time)';
    } else if (mode === 'offset') {
        return `⏱️ Offset (Thread 2 starts ${delay}ms after Thread 1)`;
    } else if (mode === 'interleaved') {
        return '🔄 Interleaved (alternate iterations between threads)';
    }
    return mode;
}

// Show concurrent test results
function showConcurrentTestResults(t1Config, t2Config, t1Results, t2Results, logs, totalTime, syncMode) {
    const t1Success = t1Results.filter(r => r.status === 'PASS' || r.status === 'CONNECTED' || r.status === 'DISCONNECTED' || r.status === 'COMPLETED').length;
    const t2Success = t2Results.filter(r => r.status === 'PASS' || r.status === 'CONNECTED' || r.status === 'DISCONNECTED' || r.status === 'COMPLETED').length;
    const t1Total = t1Results.length;
    const t2Total = t2Results.length;
    
    outputArea.innerHTML = `
        <div style="padding: 20px; background: #f8f9fa; border-left: 4px solid #8b5cf6;">
            <h3>✅ Concurrent Test Completed</h3>
            <p><strong>Sync Mode:</strong> ${getSyncModeDescription(syncMode, 0)}</p>
            <p><strong>Total Time:</strong> ${totalTime} seconds</p>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0;">
                <div style="padding: 15px; background: #eff6ff; border-left: 3px solid #3b82f6; border-radius: 4px;">
                    <h4 style="margin: 0 0 10px 0; color: #1e40af;">🔵 Thread 1 Results</h4>
                    <p style="margin: 5px 0;"><strong>Operation:</strong> ${getThreadDescription(t1Config)}</p>
                    <p style="margin: 5px 0;"><strong>Successful:</strong> ${t1Success} / ${t1Total}</p>
                    <p style="margin: 5px 0;"><strong>Success Rate:</strong> ${t1Total > 0 ? ((t1Success/t1Total)*100).toFixed(1) : 0}%</p>
                </div>
                
                <div style="padding: 15px; background: #ecfdf5; border-left: 3px solid #10b981; border-radius: 4px;">
                    <h4 style="margin: 0 0 10px 0; color: #047857;">🟢 Thread 2 Results</h4>
                    <p style="margin: 5px 0;"><strong>Operation:</strong> ${getThreadDescription(t2Config)}</p>
                    <p style="margin: 5px 0;"><strong>Successful:</strong> ${t2Success} / ${t2Total}</p>
                    <p style="margin: 5px 0;"><strong>Success Rate:</strong> ${t2Total > 0 ? ((t2Success/t2Total)*100).toFixed(1) : 0}%</p>
                </div>
            </div>
            
            <div style="margin-top: 15px;">
                <button onclick="downloadConcurrentTestV2Results()" style="padding: 10px 20px; background: #2563eb; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600;">
                    💾 Download Full Report
                </button>
            </div>
        </div>
    `;
    
    // Store results for download
    window.lastConcurrentTestV2 = {
        thread1Config: t1Config,
        thread2Config: t2Config,
        thread1Results: t1Results,
        thread2Results: t2Results,
        logs: logs,
        totalTime: totalTime,
        syncMode: syncMode
    };
}

// Download concurrent test V2 results
window.downloadConcurrentTestV2Results = async function() {
    const data = window.lastConcurrentTestV2;
    if (!data) {
        alert('No test results available');
        return;
    }
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    const filename = `Concurrent_Test_2Thread_${timestamp}.txt`;
    
    let report = '='.repeat(70) + '\n';
    report += 'UCSI DECODER - CONCURRENT TEST (2-THREAD) RESULTS\n';
    report += '='.repeat(70) + '\n\n';
    report += `Date: ${new Date().toLocaleString()}\n`;
    report += `Test Type: Concurrent (2 Independent Threads)\n`;
    report += `Sync Mode: ${getSyncModeDescription(data.syncMode, 0)}\n`;
    report += `Total Time: ${data.totalTime} seconds\n\n`;
    
    report += 'THREAD 1 CONFIGURATION:\n';
    report += `  Operation: ${getThreadDescription(data.thread1Config)}\n`;
    report += `  Iterations: ${data.thread1Config.iterations}\n`;
    report += `  Delay: ${data.thread1Config.delay}ms\n\n`;
    
    report += 'THREAD 2 CONFIGURATION:\n';
    report += `  Operation: ${getThreadDescription(data.thread2Config)}\n`;
    report += `  Iterations: ${data.thread2Config.iterations}\n`;
    report += `  Delay: ${data.thread2Config.delay}ms\n\n`;
    
    const t1Success = data.thread1Results.filter(r => r.status === 'PASS' || r.status === 'CONNECTED' || r.status === 'DISCONNECTED' || r.status === 'COMPLETED').length;
    const t2Success = data.thread2Results.filter(r => r.status === 'PASS' || r.status === 'CONNECTED' || r.status === 'DISCONNECTED' || r.status === 'COMPLETED').length;
    
    report += 'RESULTS SUMMARY:\n';
    report += `  Thread 1: ${t1Success}/${data.thread1Results.length} successful\n`;
    report += `  Thread 2: ${t2Success}/${data.thread2Results.length} successful\n\n`;
    
    report += '='.repeat(70) + '\n';
    report += 'EXECUTION LOGS (Chronological)\n';
    report += '='.repeat(70) + '\n\n';
    
    data.logs.forEach(log => {
        report += `[${log.timestamp}] ${log.thread}: ${log.message}\n`;
    });
    
    report += '\n' + '='.repeat(70) + '\n';
    report += 'END OF REPORT\n';
    report += '='.repeat(70) + '\n';
    
    try {
        const response = await fetch('/save_test_results', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                filename: filename,
                content: report
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`✅ Report saved successfully!\n\nLocation: ${result.filepath}`);
        } else {
            alert(`❌ Failed to save report: ${result.error}`);
        }
    } catch (error) {
        alert(`❌ Error saving report: ${error.message}`);
    }
};

// ==============================================
// Sudo Password Dialog (Linux Only)
// ==============================================

// Update Linux device status
function updateLinuxDeviceStatus() {
    const statusDiv = document.getElementById('deviceStatus');
    if (!statusDiv) return;
    
    if (!platformInfo.is_linux) return;
    
    const ucsiPath = platformInfo.ucsi_path;
    
    // Show status based on UCSI path availability
    statusDiv.innerHTML = `<span class="status-icon">✓</span><span class="status-text"><strong style="color: #28a745;">UCSI enabled in debugfs</strong> - Path: ${ucsiPath}</span>`;
    statusDiv.style.background = '#d4edda';
    statusDiv.style.borderColor = '#28a745';
    
    console.log('Linux device status updated:', ucsiPath);
}

function showSudoDialog() {
    const overlay = document.getElementById('sudoDialogOverlay');
    const passwordInput = document.getElementById('sudoPassword');
    const errorDiv = document.getElementById('sudoError');
    
    // Clear previous state
    passwordInput.value = '';
    errorDiv.style.display = 'none';
    errorDiv.textContent = '';
    
    overlay.style.display = 'flex';
    
    // Focus on password input
    setTimeout(() => passwordInput.focus(), 100);
    
    // Handle Enter key
    passwordInput.onkeypress = function(e) {
        if (e.key === 'Enter') {
            authenticateSudo();
        }
    };
}

function closeSudoDialog() {
    const overlay = document.getElementById('sudoDialogOverlay');
    overlay.style.display = 'none';
}

async function authenticateSudo() {
    const passwordInput = document.getElementById('sudoPassword');
    const errorDiv = document.getElementById('sudoError');
    const okButton = document.getElementById('sudoOk');
    
    const password = passwordInput.value.trim();
    
    if (!password) {
        errorDiv.textContent = 'Please enter your sudo password';
        errorDiv.style.display = 'block';
        return;
    }
    
    // Disable button during authentication
    okButton.disabled = true;
    okButton.textContent = 'Authenticating...';
    errorDiv.style.display = 'none';
    
    try {
        const response = await fetch('/api/sudo-auth', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ password: password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Authentication successful
            closeSudoDialog();
            
            // Update UCSI status if provided
            if (data.ucsi_status) {
                console.log('UCSI Status:', data.ucsi_status);
            }
            
            // Show success message
            showNotification('✓ Authentication successful', 'success');
            
            // Refresh device manager check to show updated status (Windows only)
            if (!platformInfo.is_linux) {
                checkDeviceManager();
            }
            
            // Trigger auto port detection on Linux after authentication
            if (platformInfo.is_linux) {
                // Update device status for Linux
                updateLinuxDeviceStatus();
                
                console.log('⏰ Scheduling auto port detection in 300ms...');
                setTimeout(() => {
                    console.log('⏰ Timer fired, calling autoDetectPorts()...');
                    autoDetectPorts();
                }, 300);
            }
            
        } else {
            // Authentication failed
            errorDiv.textContent = data.error || 'Authentication failed';
            errorDiv.style.display = 'block';
            passwordInput.value = '';
            passwordInput.focus();
        }
        
    } catch (error) {
        errorDiv.textContent = 'Network error: ' + error.message;
        errorDiv.style.display = 'block';
    } finally {
        okButton.disabled = false;
        okButton.textContent = 'Authenticate';
    }
}

function showNotification(message, type = 'info') {
    // Simple notification - you can enhance this
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3498db'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        z-index: 10001;
        font-weight: 500;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Setup sudo dialog event listeners
document.addEventListener('DOMContentLoaded', function() {
    const sudoOk = document.getElementById('sudoOk');
    const sudoCancel = document.getElementById('sudoCancel');
    
    if (sudoOk) {
        sudoOk.addEventListener('click', authenticateSudo);
    }
    
    if (sudoCancel) {
        sudoCancel.addEventListener('click', closeSudoDialog);
    }
});

// ============================================================================
// UI Helper Functions
// ============================================================================

// Image Popup Modal
function setupImagePopup() {
    const logo = document.getElementById('logoImage');
    const modal = document.getElementById('imagePopupModal');
    const closeBtn = document.getElementById('imagePopupClose');

    if (logo && modal) {
        logo.addEventListener('click', function() {
            modal.classList.add('active');
        });

        closeBtn.addEventListener('click', function() {
            modal.classList.remove('active');
        });

        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });

        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && modal.classList.contains('active')) {
                modal.classList.remove('active');
            }
        });
    }
}

// Generate PPM Initialization Summary per UCSI Spec Section 6.3
function generateInitializationSummary(results) {
    const commands = results.map(r => r.command || '').map(c => c.toUpperCase());
    const decodedData = results.map(r => r.decoded || {});
    
    // Analyze command results for detailed validation
    const hasGetCapability = commands.some(c => c.includes('GET_CAPABILITY'));
    const hasGetConnectorCap = commands.some(c => c.includes('GET_CONNECTOR_CAPABILITY'));
    const hasSetCCOM = commands.some(c => c.includes('SET_CCOM'));
    const hasSetUOR = commands.some(c => c.includes('SET_UOR'));
    const hasSetPDR = commands.some(c => c.includes('SET_PDR'));
    const hasGetAltModes = commands.some(c => c.includes('GET_ALTERNATE_MODES'));
    const hasGetCAMSupported = commands.some(c => c.includes('CAM_SUPPORTED'));
    const hasGetCurrentCAM = commands.some(c => c.includes('CURRENT_CAM'));
    const hasSetNewCAM = commands.some(c => c.includes('SET_NEW_CAM'));
    
    // Define initialization steps per UCSI spec
    const steps = [
        {
            id: 1,
            description: 'PPM_RESET - Reset the PPM (Optional but recommended per Section 6.5.1)',
            required: false,
            commands: ['PPM_RESET', '1 - PPM_RESET'],
            completed: commands.some(c => c.includes('PPM_RESET')),
            note: commands.some(c => c.includes('PPM_RESET'))
                ? 'PPM reset performed - cleans previous state'
                : 'Optional - skipping is acceptable for normal operation'
        },
        {
            id: 2,
            description: 'SET_NOTIFICATION_ENABLE - Enable "Command Completed" notification (Section 6.5.5)',
            required: true,
            commands: ['SET_NOTIFICATION_ENABLE', '5 - SET_NOTIFICATION_ENABLE'],
            completed: commands.some(c => c.includes('SET_NOTIFICATION_ENABLE')),
            note: commands.some(c => c.includes('SET_NOTIFICATION_ENABLE')) 
                ? 'Command Completed notification enabled (bit 0 required)'
                : 'CRITICAL: Must enable before other commands can report completion'
        },
        {
            id: 3,
            description: 'GET_CAPABILITY - Query platform capabilities (Section 6.5.6): bNumConnectors, notifications, PD/BC versions',
            required: true,
            commands: ['GET_CAPABILITY', '6 - GET_CAPABILITY'],
            completed: hasGetCapability,
            note: hasGetCapability
                ? 'Returns: bNumConnectors, bmAttributes (PD/BC/TypeC support), bmOptionalFeatures, bNumAltModes'
                : 'CRITICAL: Provides foundation for all connector operations'
        },
        {
            id: 4,
            description: 'SET_NOTIFICATION_ENABLE - Enable additional notifications based on GET_CAPABILITY',
            required: true,
            commands: ['SET_NOTIFICATION_ENABLE', '5 - SET_NOTIFICATION_ENABLE'],
            completed: commands.filter(c => c.includes('SET_NOTIFICATION_ENABLE')).length >= 2,
            note: commands.filter(c => c.includes('SET_NOTIFICATION_ENABLE')).length >= 2
                ? 'Additional notifications enabled (should match supported notifications from GET_CAPABILITY)'
                : 'Should enable: External Supply Change, Power Op Mode, Attention, etc. based on PPM support'
        },
        {
            id: 5,
            description: 'GET_CONNECTOR_CAPABILITY - Query each connector (Section 6.5.7): Operation modes, Provider/Consumer, Swap capabilities',
            required: true,
            commands: ['GET_CONNECTOR_CAPABILITY', '7 - GET_CONNECTOR_CAPABILITY'],
            completed: hasGetConnectorCap,
            note: hasGetConnectorCap
                ? 'Returns: Operation Mode (Rp/Rd/DRP), Extended Op Mode (USB4), Provider/Consumer, Swap capabilities'
                : 'CRITICAL: Must query for each connector reported by GET_CAPABILITY'
        },
        {
            id: 6,
            description: 'GET_ALTERNATE_MODES - Query Alternate Modes (Section 6.5.11): Connector/SOP/SOP\'/SOP" SVID/MID pairs',
            required: false,
            commands: ['GET_ALTERNATE_MODES', '12 - GET_ALTERNATE_MODES'],
            completed: hasGetAltModes,
            note: hasGetAltModes
                ? 'Alternate Modes queried - returns SVID/MID pairs for requested recipient'
                : 'Optional - Only if bNumAltModes > 0 in GET_CAPABILITY. Query Recipient: Connector(0), SOP(1), SOP\'(2), SOP"(3)'
        },
        {
            id: 7,
            description: 'GET_CAM_SUPPORTED - Query currently supported Alternate Modes bitmap (Section 6.5.12)',
            required: false,
            commands: ['GET_CAM_SUPPORTED', 'CAM_SUPPORTED', '18 - GET_CAM_SUPPORTED'],
            completed: hasGetCAMSupported,
            note: hasGetCAMSupported
                ? 'Returns bitmap of currently available Alternate Modes (subset if resources in use)'
                : 'Optional - Use if Alternate Modes supported. Returns bit vector of available modes'
        },
        {
            id: 8,
            description: 'GET_CABLE_PROPERTY - Query cable details (Section 6.5.21): Cable speed, current capability, latency',
            required: false,
            commands: ['GET_CABLE_PROPERTY', '11 - GET_CABLE_PROPERTY'],
            completed: commands.some(c => c.includes('GET_CABLE_PROPERTY')),
            note: commands.some(c => c.includes('GET_CABLE_PROPERTY'))
                ? 'Cable properties queried - speed mode, current capability, plug type, latency'
                : 'Optional - Provides VDO-based cable characteristics'
        },
        {
            id: 9,
            description: 'GET_CURRENT_CAM - Query active Alternate Mode(s) (Section 6.5.13)',
            required: false,
            commands: ['GET_CURRENT_CAM', 'E - GET_CURRENT_CAM', 'CURRENT_CAM'],
            completed: hasGetCurrentCAM,
            note: hasGetCurrentCAM
                ? 'Returns offset(s) into Alternate Mode list (0xFF = no AM active)'
                : 'Optional - Shows which Alternate Mode(s) currently active'
        },
        {
            id: 10,
            description: 'SET_CCOM - Configure CC Operation Mode (Section 6.5.8): Rp Only, Rd Only, DRP, or Disabled',
            required: false,
            commands: ['SET_CCOM', '8 - SET_CCOM'],
            completed: hasSetCCOM,
            note: hasSetCCOM
                ? 'CC operation mode configured (Rp/Rd/DRP/Disabled per bit field)'
                : 'Optional - Use to override default DRP behavior if needed'
        },
        {
            id: 11,
            description: 'SET_UOR - Configure USB Operation Role (Section 6.5.9): DFP, UFP, or Accept Swap',
            required: false,
            commands: ['SET_UOR', '9 - SET_UOR'],
            completed: hasSetUOR,
            note: hasSetUOR
                ? 'USB Operation Role set - initiates data role swap if needed (DFP/UFP/Accept)'
                : 'Optional - Only if active connection exists and role change desired'
        },
        {
            id: 12,
            description: 'SET_PDR - Configure Power Direction Role (Section 6.5.10): Source, Sink, or Accept Swap',
            required: false,
            commands: ['SET_PDR', 'B - SET_PDR'],
            completed: hasSetPDR,
            note: hasSetPDR
                ? 'Power Direction set - initiates power role swap if needed (Source/Sink/Accept)'
                : 'Optional - Only if PD-capable connection exists and role change desired'
        },
        {
            id: 13,
            description: 'SET_NEW_CAM - Enter/Exit Alternate Mode (Section 6.5.14): Configure connector for specific AM',
            required: false,
            commands: ['SET_NEW_CAM', 'F - SET_NEW_CAM'],
            completed: hasSetNewCAM,
            note: hasSetNewCAM
                ? 'Alternate Mode configured - Enter(1)/Exit(0) specified mode with AM-specific data'
                : 'Optional - Use to enter specific Alternate Mode (DP, TBT, etc.) or exit with offset 0xFF'
        },
        {
            id: 14,
            description: 'GET_PDOS - Query Power Data Objects (Section 6.5.15): Sink/Source capabilities',
            required: false,
            commands: ['GET_PDOS', '10 - GET_PDOS'],
            completed: commands.some(c => c.includes('GET_PDOS') || c.includes('GET_PDO')),
            note: commands.some(c => c.includes('GET_PDOS') || c.includes('GET_PDO'))
                ? 'PDOs queried - Source (Max/Current/Advertised) or Sink capabilities, SPR/EPR range'
                : 'Optional - Returns up to 4 PDOs per request. Supports Partner PDO, Source Capabilities Type, Range selection'
        },
        {
            id: 15,
            description: 'GET_CONNECTOR_STATUS - Query connector state (Section 6.5.17): Connection, power, orientation',
            required: false,
            commands: ['GET_CONNECTOR_STATUS', 'C - GET_CONNECTOR_STATUS'],
            completed: commands.some(c => c.includes('CONNECTOR_STATUS')),
            note: commands.some(c => c.includes('CONNECTOR_STATUS'))
                ? 'Status queried - Returns 19 bytes: Connect status, Power op mode, RDO, Battery charging, Current/Voltage readings'
                : 'Optional - Comprehensive status: Connector changes, Power direction, Partner type/flags, Provider limits, Orientation'
        },
        {
            id: 16,
            description: 'GET_ERROR_STATUS - Query error details (Section 6.5.18): Diagnose command failures',
            required: false,
            commands: ['GET_ERROR_STATUS', '13 - GET_ERROR_STATUS'],
            completed: commands.some(c => c.includes('ERROR_STATUS')),
            note: commands.some(c => c.includes('ERROR_STATUS'))
                ? 'Error status retrieved - 16-bit bitmap with failure reasons (unrecognized cmd, invalid params, etc.)'
                : 'Optional - Use after Error Indicator set. Returns: Unrecognized command, CC comm error, Swap rejected, etc.'
        },
        {
            id: 17,
            description: 'SET_POWER_LEVEL - Configure max power (Section 6.5.19): Limit negotiable power for connection',
            required: false,
            commands: ['SET_POWER_LEVEL', '14 - SET_POWER_LEVEL'],
            completed: commands.some(c => c.includes('POWER_LEVEL')),
            note: commands.some(c => c.includes('POWER_LEVEL'))
                ? 'Power level configured - Max negotiable power in 0.5W/1.0W units, Type-C current, Operating current/voltage'
                : 'Optional - Only for active connections. Triggers renegotiation if needed. Reset on PPM/connector reset or detach'
        },
        {
            id: 18,
            description: 'GET_PD_MESSAGE - Retrieve PD messages (Section 6.5.20): Extended capabilities, battery status, VDM',
            required: false,
            commands: ['GET_PD_MESSAGE', '15 - GET_PD_MESSAGE'],
            completed: commands.some(c => c.includes('PD_MESSAGE')),
            note: commands.some(c => c.includes('PD_MESSAGE'))
                ? 'PD message retrieved - Sink/Source Caps Extended, Battery Cap/Status, Discover Identity, Revision'
                : 'Optional - Query from Connector(0)/SOP(1)/SOP\'(2)/SOP"(3). Returns chunked messages merged into single response'
        },
        {
            id: 19,
            description: 'GET_ATTENTION_VDO - Get Attention VDO (Section 6.5.21): Retrieve VDO after ATTENTION from port partner',
            required: false,
            commands: ['GET_ATTENTION_VDO', '21 - GET_ATTENTION_VDO'],
            completed: commands.some(c => c.includes('ATTENTION_VDO')),
            note: commands.some(c => c.includes('ATTENTION_VDO'))
                ? 'Attention VDO retrieved - Alt Mode Index, VDM Header, VDO, Sequence number for ordering'
                : 'Optional - Returns up to 33 bytes: Alt Mode index (0xFF if none), Number of VDOs (0-1), VDM Header, VDO data'
        },
        {
            id: 20,
            description: 'GET_CAM_CS - Get Current Alternate Mode Config/Status (Section 6.5.22): DP_SID and status',
            required: false,
            commands: ['GET_CAM_CS', '22 - GET_CAM_CS'],
            completed: commands.some(c => c.includes('CAM_CS')),
            note: commands.some(c => c.includes('CAM_CS'))
                ? 'Current Alt Mode config retrieved - Index, Status (Alt Mode specific), N VDOs with configuration data'
                : 'Optional - Query after GET_CURRENT_CAM. Returns: Alt Mode index, Status field (mode-specific), VDO array[N]'
        },
        {
            id: 21,
            description: 'LPM_FIRMWARE_UPDATE_REQUEST - Update LPM firmware (Section 6.5.23): PDFU mechanism',
            required: false,
            commands: ['LPM_FW_UPDATE_REQUEST', 'LPM_FIRMWARE_UPDATE'],
            completed: commands.some(c => c.includes('LPM_FW') || c.includes('FIRMWARE_UPDATE')),
            note: commands.some(c => c.includes('LPM_FW') || c.includes('FIRMWARE_UPDATE'))
                ? 'Firmware update initiated - Direction (OPM-LPM/Port/Cable/From Partner), Data chunks with index, End of Message flag'
                : 'Optional - Factory use. Supports broadcast to all LPMs (connector 7Fh). Chunked with Data Index sync, 255 byte max'
        },
        {
            id: 22,
            description: 'SECURITY_REQUEST - Authenticate USB PD Source/Sink (Section 6.5.24): USBAUTH protocol',
            required: false,
            commands: ['SECURITY_REQUEST', '24 - SECURITY_REQUEST'],
            completed: commands.some(c => c.includes('SECURITY_REQUEST')),
            note: commands.some(c => c.includes('SECURITY_REQUEST'))
                ? 'Authentication request processed - Direction, Auth Protocol Rev, Auth Message type, Data chunks with indexing'
                : 'Optional - Prevent malicious access. Direction: OPM-LPM/Port/Cable/From Partner. Chunked messages, 255 byte max'
        },
        {
            id: 23,
            description: 'SET_RETIMER_MODE - Configure re-timer mode (Section 6.5.25): FW update, calibration',
            required: false,
            commands: ['SET_RETIMER_MODE', '25 - SET_RETIMER_MODE'],
            completed: commands.some(c => c.includes('RETIMER_MODE')),
            note: commands.some(c => c.includes('RETIMER_MODE'))
                ? 'Re-timer mode set - Re-timer# (1-3), State (Off/On/LPM/Compliance/Flash), Functional Mode (USB/TBT/DP), Gain, Orientation'
                : 'Optional - Up to 2 re-timers. States: Off, Force Power, LPM, Compliance, Flashing. Modes: USB3.2/USB4/TBT/DP variants'
        },
        {
            id: 24,
            description: 'SET_SINK_PATH - Enable/disable sink path (Section 6.5.26): Control power from port partner',
            required: false,
            commands: ['SET_SINK_PATH', '26 - SET_SINK_PATH'],
            completed: commands.some(c => c.includes('SINK_PATH')),
            note: commands.some(c => c.includes('SINK_PATH'))
                ? 'Sink path configured - Enabled(1) or Disabled(0) for power consumption from port partner'
                : 'Optional - Enable=1, Disable=0. Error if LPM is source mode or no partner connected. Use GET_ERROR_STATUS for details'
        },
        {
            id: 25,
            description: 'CHUNKING_SUPPORT - Query max chunk size (Section 6.5.27): MESSAGE_IN/OUT chunking',
            required: false,
            commands: ['CHUNKING_SUPPORT', '27 - CHUNKING_SUPPORT'],
            completed: commands.some(c => c.includes('CHUNKING_SUPPORT')),
            note: commands.some(c => c.includes('CHUNKING_SUPPORT'))
                ? 'Chunking size reported - Max bytes supported by LPM/PPM for MESSAGE_IN/OUT transfers'
                : 'Optional - Not Supported=use UCSI spec max. Connector 0=broadcast to all LPMs, returns lowest size. Min 16 bytes recommended'
        },
        {
            id: 26,
            description: 'SET_PDOS - Overwrite Source/Sink PDOs (Section 6.5.28): SPR or EPR range',
            required: false,
            commands: ['SET_PDOS', '28 - SET_PDOS'],
            completed: commands.some(c => c.includes('SET_PDOS')),
            note: commands.some(c => c.includes('SET_PDOS'))
                ? 'PDOs updated - Source/Sink Capabilities overwritten, Explicit Contract renegotiated if needed'
                : 'Optional - Atomic sequence with End of Message flag. Supersedes SET_POWER_LEVEL. Max 7 PDOs for SPR. Chunked, Data Index sync'
        },
        {
            id: 27,
            description: 'VENDOR_DEFINED_COMMAND - Vendor-specific command (Section 6.5.29): Custom OPM/PPM/LPM exchange',
            required: false,
            commands: ['VENDOR_DEFINED_COMMAND', 'VDC', '29 - VENDOR_DEFINED'],
            completed: commands.some(c => c.includes('VENDOR_DEFINED') || c.includes('VDC')),
            note: commands.some(c => c.includes('VENDOR_DEFINED') || c.includes('VDC'))
                ? 'Vendor command executed - VID, PID, Vendor Defined Command (5 bits), VDC Structure Version'
                : 'Optional - Connector 0=PPM target, else LPM. Contains VID, PID, Command (vendor-defined), Structure Version'
        },
        {
            id: 28,
            description: 'GET_LPM_PPM_INFO - Query HW/FW versions (Section 6.5.30): Version information',
            required: false,
            commands: ['GET_LPM_PPM_INFO', '30 - GET_LPM_PPM_INFO'],
            completed: commands.some(c => c.includes('LPM_PPM_INFO')),
            note: commands.some(c => c.includes('LPM_PPM_INFO'))
                ? 'LPM/PPM info retrieved - VID, PID, XID, FW Version (Upper/Lower), HW Version'
                : 'Optional - Connector 0=PPM, else LPM. Returns 16 bytes: VID, PID, XID, FW versions, HW version'
        },
        {
            id: 29,
            description: 'SET_USB - Enable/disable USB modes (Section 6.5.31): USB3/USB4 configuration',
            required: false,
            commands: ['SET_USB', '31 - SET_USB'],
            completed: commands.some(c => c.includes('SET_USB')),
            note: commands.some(c => c.includes('SET_USB'))
                ? 'USB modes configured - USB3 Enable/Disable, USB4 Enable/Disable, EUDO (Enter USB Data Object)'
                : 'Optional - Stop/Start advertising modes. Triggers Data Reset if needed. EUDO for USB4. Reset on LPM reset to defaults'
        },
        {
            id: 30,
            description: 'READ_POWER_LEVEL - Read peak/average power (Section 6.5.32): Source mode measurements',
            required: false,
            commands: ['READ_POWER_LEVEL', '32 - READ_POWER_LEVEL'],
            completed: commands.some(c => c.includes('READ_POWER_LEVEL')),
            note: commands.some(c => c.includes('READ_POWER_LEVEL'))
                ? 'Power measurements started - Time to Read (100ms units), Time Interval between readings (5ms units)'
                : 'Optional - Source mode only. Sets CCI when ready. Data in GET_CONNECTOR_STATUS. Time to Read: 0=100ms, 1=200ms. Interval: 1bit=5ms'
        },
        {
            id: 31,
            description: 'ACK_CC_CI - Acknowledge command completions and notifications (Section 6.5.4)',
            required: true,
            commands: ['ACK_CC_CI', '4 - ACK_CC_CI'],
            completed: commands.some(c => c.includes('ACK_CC_CI')),
            note: commands.some(c => c.includes('ACK_CC_CI'))
                ? 'Command/Connector Change acknowledgments sent (bit 16=Connector Change, bit 17=Command Complete)'
                : 'REQUIRED: Must acknowledge after each command completion and connector change event'
        }
    ];
    
    // Calculate compliance metrics
    const totalRequired = steps.filter(s => s.required).length;
    const completedRequired = steps.filter(s => s.required && s.completed).length;
    const totalOptional = steps.filter(s => !s.required).length;
    const completedOptional = steps.filter(s => !s.required && s.completed).length;
    
    return {
        steps: steps,
        totalRequired: totalRequired,
        completedRequired: completedRequired,
        totalOptional: totalOptional,
        completedOptional: completedOptional
    };
}

// Save current result as PDF with table formatting
function saveCurrentResultPDF() {
    // Check if jsPDF is available
    if (typeof jspdf === 'undefined') {
        alert('PDF library not loaded. Please refresh the page and try again.');
        return;
    }
    
    // Check if we have accumulated results or just a single result
    let resultsToSave;
    if (allDecodedResults.length > 0) {
        resultsToSave = allDecodedResults;
    } else if (currentDecodedResult) {
        resultsToSave = [{
            command: selectedCommand,
            port: selectedPort,
            timestamp: new Date().toLocaleString(),
            decoded: currentDecodedResult
        }];
    } else {
        resultsToSave = [];
    }
    
    if (resultsToSave.length === 0) {
        alert('No results to save. Please run a command first.');
        return;
    }
    
    const timestamp = new Date().toISOString().replace(/:/g, '-').split('.')[0];
    const filename = resultsToSave.length === 1 
        ? `UCSI_Decode_${resultsToSave[0].command.replace(/\s/g, '_')}_Port${resultsToSave[0].port}_${timestamp}.pdf`
        : `UCSI_Decode_AllResults_${timestamp}.pdf`;
    
    try {
        const { jsPDF } = jspdf;
        const doc = new jsPDF({
            orientation: 'portrait',
            unit: 'mm',
            format: 'a4'
        });
        
        let yPos = 15;
        const pageWidth = doc.internal.pageSize.getWidth();
        const pageHeight = doc.internal.pageSize.getHeight();
        const margin = 15;
        const maxWidth = pageWidth - (2 * margin);
        
        // Title
        doc.setFontSize(18);
        doc.setFont(undefined, 'bold');
        doc.text('UCSI DECODER - DECODED RESULTS', margin, yPos);
        
        yPos += 10;
        doc.setFontSize(10);
        doc.setFont(undefined, 'normal');
        doc.text(`Total Results: ${resultsToSave.length}`, margin, yPos);
        yPos += 5;
        doc.text(`Generated: ${new Date().toLocaleString()}`, margin, yPos);
        yPos += 5;
        doc.text(`UCSI Version: ${ucsiVersionSelect ? ucsiVersionSelect.value : detectedVersion}`, margin, yPos);
        yPos += 10;
        
        // ===== PPM INITIALIZATION SUMMARY (Per UCSI Spec Section 6.3) =====
        doc.setFontSize(14);
        doc.setFont(undefined, 'bold');
        doc.setTextColor(37, 99, 235); // Blue color
        doc.text('PPM INITIALIZATION FLOW SUMMARY', margin, yPos);
        doc.setTextColor(0, 0, 0); // Reset to black
        yPos += 7;
        
        // Generate initialization summary
        const initSummary = generateInitializationSummary(resultsToSave);
        
        doc.setFontSize(9);
        doc.setFont(undefined, 'normal');
        
        // Draw summary box
        const boxStartY = yPos;
        const boxPadding = 3;
        
        // Step-by-step analysis
        initSummary.steps.forEach((step, idx) => {
            if (yPos > pageHeight - 25) {
                doc.addPage();
                yPos = 15;
            }
            
            // Step status indicator
            const statusSymbol = step.completed ? '✓' : '✗';
            const statusColor = step.completed ? [34, 197, 94] : [239, 68, 68]; // Green or Red
            
            doc.setTextColor(...statusColor);
            doc.setFont(undefined, 'bold');
            doc.text(`${statusSymbol} Test ${idx + 1}:`, margin, yPos);
            
            doc.setTextColor(0, 0, 0);
            doc.setFont(undefined, 'normal');
            const stepText = doc.splitTextToSize(step.description, maxWidth - 20);
            doc.text(stepText, margin + 20, yPos);
            yPos += stepText.length * 4;
            
            if (step.note) {
                doc.setFont(undefined, 'italic');
                doc.setFontSize(8);
                const noteText = doc.splitTextToSize(`   Note: ${step.note}`, maxWidth - 20);
                doc.text(noteText, margin + 20, yPos);
                yPos += noteText.length * 3.5;
                doc.setFontSize(9);
            }
            yPos += 2;
        });
        
        // Overall compliance summary
        yPos += 3;
        if (yPos > pageHeight - 30) {
            doc.addPage();
            yPos = 15;
        }
        
        doc.setFontSize(10);
        doc.setFont(undefined, 'bold');
        doc.text('Initialization Compliance Summary:', margin, yPos);
        yPos += 6;
        
        doc.setFontSize(9);
        doc.setFont(undefined, 'normal');
        doc.text(`• Required Steps Completed: ${initSummary.completedRequired}/${initSummary.totalRequired}`, margin + 5, yPos);
        yPos += 5;
        doc.text(`• Optional Steps Completed: ${initSummary.completedOptional}/${initSummary.totalOptional}`, margin + 5, yPos);
        yPos += 5;
        
        const compliancePercent = Math.round((initSummary.completedRequired / initSummary.totalRequired) * 100);
        const complianceColor = compliancePercent >= 80 ? [34, 197, 94] : compliancePercent >= 50 ? [234, 179, 8] : [239, 68, 68];
        doc.setTextColor(...complianceColor);
        doc.setFont(undefined, 'bold');
        doc.text(`• Overall Compliance: ${compliancePercent}%`, margin + 5, yPos);
        doc.setTextColor(0, 0, 0);
        yPos += 8;
        
        // Draw separator line
        doc.setDrawColor(200, 200, 200);
        doc.line(margin, yPos, pageWidth - margin, yPos);
        yPos += 8;
        
        // Iterate through all results
        resultsToSave.forEach((result, index) => {
            // Check if we need a new page
            if (yPos > pageHeight - 30) {
                doc.addPage();
                yPos = 15;
            }
            
            // Result header
            doc.setFontSize(14);
            doc.setFont(undefined, 'bold');
            doc.text(`RESULT #${index + 1}`, margin, yPos);
            yPos += 8;
            
            doc.setFontSize(10);
            doc.setFont(undefined, 'normal');
            doc.text(`Command: ${result.command}`, margin, yPos);
            yPos += 5;
            doc.text(`Port: ${result.port}`, margin, yPos);
            yPos += 5;
            doc.text(`Timestamp: ${result.timestamp}`, margin, yPos);
            yPos += 8;
            
            // Raw Data section
            doc.setFont(undefined, 'bold');
            doc.text('RAW DATA', margin, yPos);
            yPos += 5;
            doc.setFont(undefined, 'normal');
            
            if (result.decoded.raw_hex) {
                doc.text(`Length: ${result.decoded.raw_len || 'N/A'} bytes`, margin, yPos);
                yPos += 5;
                
                // Wrap long hex strings
                const hexLines = doc.splitTextToSize(`Hex: ${result.decoded.raw_hex}`, maxWidth);
                hexLines.forEach(line => {
                    if (yPos > pageHeight - 20) {
                        doc.addPage();
                        yPos = 15;
                    }
                    doc.text(line, margin, yPos);
                    yPos += 5;
                });
            } else if (result.decoded.status || result.decoded.message) {
                doc.text(`Status: ${result.decoded.status || 'N/A'}`, margin, yPos);
                yPos += 5;
                if (result.decoded.message) {
                    const msgLines = doc.splitTextToSize(`Message: ${result.decoded.message}`, maxWidth);
                    msgLines.forEach(line => {
                        if (yPos > pageHeight - 20) {
                            doc.addPage();
                            yPos = 15;
                        }
                        doc.text(line, margin, yPos);
                        yPos += 5;
                    });
                }
            }
            
            yPos += 3;
            
            // DECODED FIELDS section with table
            if (yPos > pageHeight - 40) {
                doc.addPage();
                yPos = 15;
            }
            
            doc.setFont(undefined, 'bold');
            doc.text('DECODED FIELDS', margin, yPos);
            yPos += 5;
            
            // Extract table data from decoded result
            const tableData = extractTableDataForPDF(result.decoded);
            
            if (tableData.length > 0) {
                doc.autoTable({
                    startY: yPos,
                    head: [['Offset', 'Field', 'Size (Bits)', 'Value', 'Interpretation']],
                    body: tableData,
                    theme: 'grid',
                    styles: {
                        fontSize: 8,
                        cellPadding: 2,
                        overflow: 'linebreak',
                        textColor: [0, 0, 0]  // Black text
                    },
                    headStyles: {
                        fillColor: [37, 99, 235],
                        textColor: 255,
                        fontStyle: 'bold',
                        halign: 'center',
                        fontSize: 9
                    },
                    columnStyles: {
                        0: { cellWidth: 15, halign: 'center', fontStyle: 'bold', fontSize: 10 },  // Offset - bold, larger
                        1: { cellWidth: 45, fontStyle: 'bold', fontSize: 9 },  // Field - bold, size 9
                        2: { cellWidth: 20, halign: 'center' },  // Size
                        3: { cellWidth: 35 },  // Value
                        4: { cellWidth: 'auto' }  // Interpretation
                    },
                    margin: { left: margin, right: margin },
                    didDrawPage: function(data) {
                        yPos = data.cursor.y;
                    }
                });
                
                yPos = doc.lastAutoTable.finalY + 10;
            } else {
                yPos += 5;
            }
        });
        
        // Save the PDF
        doc.save(filename);
        showNotification(`Result${resultsToSave.length > 1 ? 's' : ''} saved as PDF: ${filename}`, 'success');
        
    } catch (error) {
        console.error('PDF generation error:', error);
        alert('Error generating PDF: ' + error.message);
    }
}

// Extract table data from decoded result for PDF
function extractTableDataForPDF(decoded) {
    const tableData = [];
    
    // Helper to process fields array
    function processFields(fields, indent = 0) {
        if (!fields || !Array.isArray(fields)) return;
        
        fields.forEach(field => {
            const indentStr = '  '.repeat(indent);
            
            if (field.children && field.children.length > 0) {
                // Parent field with children
                tableData.push([
                    field.offset || '',
                    indentStr + (field.field || ''),
                    field.size || '',
                    field.value || '',
                    field.interpretation || ''
                ]);
                processFields(field.children, indent + 1);
            } else {
                // Leaf field
                tableData.push([
                    field.offset || '',
                    indentStr + (field.field || ''),
                    field.size || '',
                    field.value || '',
                    field.interpretation || ''
                ]);
            }
        });
    }
    
    // Process main fields
    if (decoded.fields && Array.isArray(decoded.fields)) {
        processFields(decoded.fields);
    }
    
    // Include special fields if present
    if (decoded.Command_Status) {
        tableData.push(['', 'Command Status', '', decoded.Command_Status, '']);
    }
    if (decoded.Description) {
        tableData.push(['', 'Description', '', decoded.Description, '']);
    }
    if (decoded.How_It_Works) {
        tableData.push(['', 'How It Works', '', decoded.How_It_Works, '']);
    }
    if (decoded.Important_Note) {
        tableData.push(['', 'Important Note', '', decoded.Important_Note, '']);
    }
    if (decoded.Next_Step) {
        tableData.push(['', 'Next Step', '', decoded.Next_Step, '']);
    }
    
    return tableData;
}

// ============================================================================
// VDC Loopback Test
// ============================================================================

async function runVdcLoopbackTest() {
    showLoading(true);
    outputArea.innerHTML = '<div style="padding: 20px; text-align: center;">⏳ Running VDC 255-byte loopback test...</div>';

    try {
        const response = await fetch('/api/vdc_loopback_test', { method: 'POST' });
        const data = await response.json();
        showLoading(false);

        // Populate the Hex Response field just like other commands
        hexResponseInput.value = data.hex_response || '';

        const passed = data.success;

        if (data.decoded) {
            displayDecodedResult(data.decoded);

            // Append VDC check table after the standard decoded output
            const checks = data.checks || {};
            const tick = '✅', cross = '❌';
            const statusColor = passed ? '#16a34a' : '#dc2626';
            const statusLabel = passed ? '✅ PASS' : '❌ FAIL';

            const rows = [
                ['Command completed',                  checks.command_completed ? tick : cross],
                ['Success header (87 80 01 00 00 0a)', checks.success_header    ? tick : cross],
                ['Checksum match (81 7e 00 00)',       checks.checksum_match    ? tick : cross],
                ['Error indicator (expect none)',      checks.error_indicator   ? cross : tick],
            ].map(([label, result]) =>
                `<tr>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #334155; color: #e2e8f0;">${label}</td>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #334155; text-align: center; font-size: 16px;">${result}</td>
                </tr>`
            ).join('');

            const extra = document.createElement('div');
            extra.innerHTML = `
                <hr style="margin: 20px 0; border-color: #374151;">
                <div style="background:#1e293b; padding:16px; border-radius:8px; margin-bottom:10px; border-left:4px solid ${statusColor};">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                        <h3 style="margin:0; color:#60a5fa; font-size:16px;">🔁 VDC Loopback Checks</h3>
                        <span style="background:${statusColor}; color:#fff; padding:3px 14px; border-radius:4px; font-weight:bold;">${statusLabel}</span>
                    </div>
                    <table style="width:100%; border-collapse:collapse; font-size:13px;">
                        <thead>
                            <tr style="background:#0f172a;">
                                <th style="padding:8px 12px; text-align:left; color:#94a3b8;">Check</th>
                                <th style="padding:8px 12px; text-align:center; color:#94a3b8;">Result</th>
                            </tr>
                        </thead>
                        <tbody>${rows}</tbody>
                    </table>
                    <details style="margin-top:12px;">
                        <summary style="cursor:pointer; color:#94a3b8; font-size:12px; user-select:none;">▶ Raw output</summary>
                        <pre style="margin-top:8px; font-size:11px; background:#020617; color:#22d3ee; padding:12px; border-radius:4px; overflow-x:auto; white-space:pre-wrap;">${escapeHtml(data.raw_output || '')}</pre>
                    </details>
                </div>`;
            outputArea.appendChild(extra);
        } else {
            outputArea.innerHTML = `<div style="padding:20px; background:#f8d7da; border-left:4px solid #dc3545;">
                <h3 style="color:#721c24; margin-top:0;">❌ VDC Loopback Failed</h3>
                <p>${escapeHtml(data.error || 'Unknown error')}</p>
                <pre style="font-size:11px; background:#020617; color:#22d3ee; padding:12px; border-radius:4px; overflow-x:auto; white-space:pre-wrap;">${escapeHtml(data.raw_output || '')}</pre>
            </div>`;
        }

        // ── Mirror exactly what executeCommand() does after a successful run ──

        // 1. Current decoded result (for Save Last Result / Copy)
        currentDecodedResult = data.decoded || {};

        // 2. History panel
        addToHistory('20 - VENDOR_DEFINED', data.hex_response || '', data.decoded, selectedPort);

        // 3. Accumulated results (for Save All Results / PDF)
        allDecodedResults.push({
            command: '20 - VENDOR_DEFINED',
            port: selectedPort,
            timestamp: new Date().toLocaleString(),
            decoded: data.decoded,
            hex_response: data.hex_response || ''
        });

        // 4. testResults / portResults (for Results Summary, Save Summary, pie chart)
        const status = passed ? 'passed' : 'failed';
        const statusMsg = passed ? 'VDC loopback passed' : (data.decoded && data.decoded.error ? data.decoded.error : 'VDC loopback failed');

        if (!portResults[selectedPort]) {
            portResults[selectedPort] = { passed: 0, failed: 0, notRun: 0, total: 0, details: [] };
        }
        if (passed) {
            portResults[selectedPort].passed++;
            testResults.passed++;
        } else {
            portResults[selectedPort].failed++;
            testResults.failed++;
        }
        portResults[selectedPort].total++;
        testResults.total++;

        const detailEntry = {
            command: '20 - VENDOR_DEFINED',
            port: selectedPort,
            status: status.toUpperCase(),
            message: statusMsg
        };
        portResults[selectedPort].details.push(detailEntry);
        testResults.details.push(detailEntry);

        // 5. Command item visual feedback
        const commandItems = document.querySelectorAll('.command-item');
        commandItems.forEach(item => {
            if (item.dataset.cmdKey === '20 - VENDOR_DEFINED') {
                item.classList.remove('cmd-passed', 'cmd-failed', 'cmd-na');
                item.classList.add(passed ? 'cmd-passed' : 'cmd-failed');
            }
        });

        // 6. Pie chart update
        updateResultsChart();

        // 7. Show Save / Copy buttons
        document.getElementById('saveResultBtnGroup').style.display = 'flex';
        document.getElementById('copyResultBtn').style.display = 'inline-block';

        showNotification(passed ? 'VDC loopback PASSED' : 'VDC loopback FAILED', passed ? 'success' : 'error');

    } catch (err) {
        showLoading(false);
        outputArea.innerHTML = `<div style="padding:20px; background:#f8d7da; border-left:4px solid #dc3545;">
            <h3 style="color:#721c24; margin-top:0;">❌ VDC Loopback Test Error</h3>
            <p>${escapeHtml(err.message)}</p>
        </div>`;
    }
}

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

// ---------------------------------------------------------------------------
// Infrastructure visual interactions
// ---------------------------------------------------------------------------

function setupInfrastructureVisuals() {
    setupScrollReveal();
    setupHeroParallax();
    setupParticleField();
    setupProductShowcaseInteractions();
}

function setupScrollReveal() {
    const elements = document.querySelectorAll('.reveal-on-scroll');
    if (!elements.length || typeof IntersectionObserver === 'undefined') {
        return;
    }

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add('revealed');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.12,
        rootMargin: '0px 0px -30px 0px'
    });

    elements.forEach((el) => observer.observe(el));
}

function setupHeroParallax() {
    const hero = document.getElementById('hero');
    const visual = document.querySelector('.product-visual');
    if (!hero || !visual) {
        return;
    }

    let frameId = null;

    hero.addEventListener('mousemove', (event) => {
        if (frameId) {
            cancelAnimationFrame(frameId);
        }
        frameId = requestAnimationFrame(() => {
            const rect = hero.getBoundingClientRect();
            const nx = (event.clientX - rect.left) / rect.width - 0.5;
            const ny = (event.clientY - rect.top) / rect.height - 0.5;
            const tx = nx * 12;
            const ty = ny * 8;
            visual.style.transform = `translate3d(${tx}px, ${ty}px, 0)`;
        });
    });

    hero.addEventListener('mouseleave', () => {
        visual.style.transform = 'translate3d(0, 0, 0)';
    });
}

function setupProductShowcaseInteractions() {
    const sampleButtons = document.querySelectorAll('.demo-sample-btn');
    const decodeSampleBtn = document.getElementById('demoDecodeBtn');
    const outputTarget = document.getElementById('outputArea');
    const commandItems = document.querySelectorAll('.command-item');
    let decodeStartTime = 0;
    let lastDecodeDurationMs = 0;

    function activateWorkflowStep(stepNumber) {
        const steps = document.querySelectorAll('.workflow-step');
        if (!steps.length) {
            return;
        }
        steps.forEach((step) => {
            const n = parseInt(step.dataset.step || '0', 10);
            if (n <= stepNumber) {
                step.classList.add('active');
            } else {
                step.classList.remove('active');
            }
        });
    }

    function updateRealMetrics() {
        const commandCountEl = document.getElementById('metricCommands');
        const accuracyEl = document.getElementById('metricAccuracy');
        const speedEl = document.getElementById('metricSpeed');
        const coverageEl = document.getElementById('metricCoverage');

        if (!commandCountEl || !accuracyEl || !speedEl || !coverageEl) {
            return;
        }

        const totalCommands = document.querySelectorAll('.command-item').length;
        const measured = (testResults.passed || 0) + (testResults.failed || 0);
        const accuracy = measured > 0 ? ((testResults.passed / measured) * 100).toFixed(1) + '%' : '--';
        const coverage = totalCommands > 0 ? Math.min(100, (testResults.total / totalCommands) * 100).toFixed(1) + '%' : '0%';
        const speed = lastDecodeDurationMs > 0 ? `${lastDecodeDurationMs.toFixed(0)} ms` : '--';

        commandCountEl.textContent = String(totalCommands);
        accuracyEl.textContent = accuracy;
        speedEl.textContent = speed;
        coverageEl.textContent = coverage;
    }

    function loadSample(sampleKey) {
        const sample = SAMPLE_DATA[sampleKey];
        if (!sample) {
            return;
        }

        // Match command by UCSI command token if available in the list.
        const token = sample.command.split(' - ')[1] || sample.command;
        const item = Array.from(commandItems).find((cmdItem) => (cmdItem.dataset.cmdKey || '').includes(token));
        if (item) {
            selectCommand(item);
        }

        if (hexResponseInput) {
            hexResponseInput.value = sample.hex;
        }

        activateWorkflowStep(1);
    }

    sampleButtons.forEach((btn) => {
        btn.addEventListener('click', () => {
            const key = btn.dataset.sample;
            loadSample(key);
        });
    });

    if (decodeSampleBtn) {
        decodeSampleBtn.addEventListener('click', () => {
            decodeStartTime = performance.now();
            activateWorkflowStep(2);
            if (decodeBtn) {
                decodeBtn.click();
            }
        });
    }

    if (decodeBtn) {
        decodeBtn.addEventListener('click', () => {
            decodeStartTime = performance.now();
            activateWorkflowStep(2);
        });
    }

    if (runCommandBtn) {
        runCommandBtn.addEventListener('click', () => {
            decodeStartTime = performance.now();
            activateWorkflowStep(2);
        });
    }

    if (outputTarget) {
        const outputObserver = new MutationObserver(() => {
            if (decodeStartTime > 0) {
                lastDecodeDurationMs = performance.now() - decodeStartTime;
                decodeStartTime = 0;
            }

            activateWorkflowStep(4);
            updateRealMetrics();
        });

        outputObserver.observe(outputTarget, { childList: true, subtree: true, characterData: true });
    }

    // Keep analysis stage visible once results/chart updates begin.
    if (resultsChart) {
        resultsChart.addEventListener('transitionstart', () => activateWorkflowStep(3));
    }

    // Initial value population.
    updateRealMetrics();
}

function setupParticleField() {
    const canvas = document.getElementById('particleCanvas');
    if (!canvas) {
        return;
    }

    const context = canvas.getContext('2d');
    if (!context) {
        return;
    }

    let width = 0;
    let height = 0;
    const maxParticles = 46;
    const particles = [];
    let animationFrame = null;

    function resizeCanvas() {
        width = window.innerWidth;
        height = window.innerHeight;
        canvas.width = width;
        canvas.height = height;
    }

    function resetParticles() {
        particles.length = 0;
        for (let i = 0; i < maxParticles; i++) {
            particles.push({
                x: Math.random() * width,
                y: Math.random() * height,
                vx: (Math.random() - 0.5) * 0.3,
                vy: (Math.random() - 0.5) * 0.3,
                radius: Math.random() * 1.8 + 0.6
            });
        }
    }

    function tick() {
        context.clearRect(0, 0, width, height);

        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];

            p.x += p.vx;
            p.y += p.vy;

            if (p.x <= 0 || p.x >= width) p.vx *= -1;
            if (p.y <= 0 || p.y >= height) p.vy *= -1;

            context.beginPath();
            context.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
            context.fillStyle = 'rgba(118, 185, 0, 0.45)';
            context.fill();

            for (let j = i + 1; j < particles.length; j++) {
                const q = particles[j];
                const dx = p.x - q.x;
                const dy = p.y - q.y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < 130) {
                    const alpha = (1 - distance / 130) * 0.14;
                    context.strokeStyle = `rgba(118, 185, 0, ${alpha})`;
                    context.lineWidth = 1;
                    context.beginPath();
                    context.moveTo(p.x, p.y);
                    context.lineTo(q.x, q.y);
                    context.stroke();
                }
            }
        }

        animationFrame = requestAnimationFrame(tick);
    }

    resizeCanvas();
    resetParticles();
    tick();

    window.addEventListener('resize', () => {
        resizeCanvas();
        resetParticles();
    });

    window.addEventListener('beforeunload', () => {
        if (animationFrame) {
            cancelAnimationFrame(animationFrame);
        }
    });
}

