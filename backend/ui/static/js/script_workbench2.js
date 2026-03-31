// script start
// script start
    <link rel="stylesheet" href="/static/css/workbench.css">
    <link rel="stylesheet" href="/static/css/modal.css">
    <style>
        .main-tab-content {
            height: 100%;
            width: 100%;
            display: none !important;
            overflow: hidden;
        }
        .main-tab-content.active {
            display: block !important;
        }
        #tab-derivatives.active {
            display: flex !important;
            flex-direction: column;
        }




        /* Main Tab Navigation */
        body {
            margin: 0;
            padding: 0;
            background: #1e1e1e;
            color: #ccc;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .main-tabs-bar {
            height: 35px;
            background: #252526;
            display: flex;
            align-items: center;
            padding-left: 10px;
            border-bottom: 1px solid #333;
            user-select: none;
        }

        .main-tab {
            padding: 8px 15px;
            cursor: pointer;
            font-size: 0.9em;
            color: #999;
            border-right: 1px solid #333;
            background: #2d2d2d;
            height: 100%;
            display: flex;
            align-items: center;
            box-sizing: border-box;
        }

        .main-tab:hover {
            background: #3e3e42;
            color: #fff;
        }

        .main-tab.active {
            background: #1e1e1e;
            color: #fff;
            border-bottom: 2px solid #007acc;
            font-weight: 500;
        }

        .tab-content-area {
            flex: 1;
            overflow: hidden;
            position: relative;
            background: #1e1e1e;
            display: flex;
            flex-direction: column;
        }





        .global-status-bar {
            height: 25px;
            background: #252526;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 15px;
            border-top: 1px solid #333;
            user-select: none;
            font-size: 12px;
            color: white;
            flex-shrink: 0;
        }

        .global-status-bar a {
            color: white;
            text-decoration: none;
        }



        /* Historical Data Styles (Merged from data_viewer.html) */
        .history-controls {
            padding: 10px 15px;
            background: #252526;
            border-bottom: 1px solid #333;
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }
        .control-group { display: flex; align-items: center; gap: 5px; }
        .control-group label { font-size: 0.85em; color: #aaa; }
        .history-input, .history-select {
            background: #3c3c3c;
            color: #ccc;
            border: 1px solid #555;
            padding: 4px 8px;
            border-radius: 3px;
        }
        .table-wrapper {
            height: calc(100% - 45px); /* Adjust based on controls height */
            overflow: auto;
            overflow-x: auto;
            position: relative;
            background: #1e1e1e;
        }
        /* Excel-like Grid */
        .data-table {
            width: max-content;
            min-width: 100%;
            border-collapse: collapse;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 13px;
            white-space: nowrap;
            color: #d4d4d4;
        }
        .data-table th, .data-table td {
            border: 1px solid #3e3e42;
            padding: 4px 8px;
            text-align: left;
        }
        .data-table th {
            background: #252526;
            position: sticky;
            top: 0;
            z-index: 10;
            font-weight: normal;
            color: #cccccc;
            border-bottom: 2px solid #007acc;
            cursor: pointer;
            user-select: none;
        }
        .data-table th:hover { background: #2d2d30; color: #fff; }
        .data-table tr { background: #1e1e1e; }
        .data-table tr:nth-child(even) { background: #1e1e1e; } /* No stripe for clean excel look, or maybe subtle */
        .data-table tr:hover { background: #2a2d2e; } /* Row selection feel */
        .data-table td { border-right: 1px solid #333; border-bottom: 1px solid #333; }

        /* Loading/Empty State */
        .data-table tr.message-row td {
            padding: 40px;
            font-size: 1.1em;
            color: #888;
            border: none;
        }
        .history-status-bar {
            padding: 5px 15px;
            background: #007acc;
            color: white;
            font-size: 0.8em;
            display: flex;
            justify-content: space-between;
            height: 25px;
            align-items: center;
        }

        /* Import Tab Styles */
        .import-container {
            padding: 20px;
            width: 100%;
            max-width: none;
            height: 100%;
            overflow: hidden; /* removed scrollbar per user request */
            display: flex;
            gap: 20px;
        }
        .import-left-panel {
            flex: 0 0 auto;
            width: 1000px;
            display: flex;
            flex-direction: column;
            overflow: hidden; /* no scrollbars anywhere in imports view per request */
        }
        .import-right-panel {
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 20px;
            min-width: 300px;
            height: 100%;
            padding-bottom: 20px;
        }
        .import-terminal {
            flex: 1;
            background-color: #0c0c0c;
            border: 1px solid #333;
            border-radius: 4px;
            padding: 10px;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 12px;
            color: #d4d4d4;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
            display: flex;
            flex-direction: column;
        }
        .import-tabs .tab-btn {
            padding: 10px 20px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
        }

        /* Common Utils */
        .btn { padding: 6px 12px; border: none; border-radius: 3px; cursor: pointer; font-size: 0.9em; }
        .btn-primary { background: #007acc; color: white; }
        .btn-primary:hover { background: #0062a3; }
        .btn-secondary { background: #3c3c3c; color: #ccc; }
        .btn-secondary:hover { background: #4e4e50; }

    </style>
</head>
<body>

    <!-- Main Tab Bar -->
    <div class="main-tabs-bar">
        <div class="main-tab active" data-target="terminal" onclick="switchMainTab('terminal')" title="Alt+T">Turtle <u>T</u>erminal</div>
        <div class="main-tab" data-target="ai_analyze" onclick="switchMainTab('ai_analyze')" title="Alt+A"><u>A</u>I-Analyze</div>
        <div class="main-tab" data-target="derivatives" onclick="switchMainTab('derivatives')" title="Derivatives Analysis">Derivatives Analysis</div>
        <div class="main-tab" data-target="history" onclick="switchMainTab('history')" title="Alt+H"><u>H</u>istorical Data</div>
        <div class="main-tab" data-target="import" onclick="switchMainTab('import')" title="Alt+I"><u>I</u>mport Data</div>
        <div class="main-tab" data-target="corporate_actions" onclick="switchMainTab('corporate_actions')" title="Alt+O">C<u>o</u>rporate Filings</div>
        <div class="main-tab" data-target="audit" onclick="switchMainTab('audit')" title="Alt+U">A<u>u</u>dit Trail</div>
        <div class="main-tab" data-target="config" onclick="switchMainTab('config')" title="Alt+C"><u>C</u>onfig</div>
    </div>

    <!-- Tab Content Container -->
    <div class="tab-content-area">

        <!-- TAB 1: TERMINAL (Original Workbench) -->
        <div id="tab-terminal" class="main-tab-content active">
            <div id="app-container" style="height:100%;">
                <!-- Left Panel -->
                <div id="left-panel">
                    <div class="lp-section" id="lp-top">
                        <div class="panel-header">Trading Edge</div>
                        <div class="panel-content" id="edge-content" style="padding:10px; font-size:0.9em; color:#ccc;"></div>
                    </div>
                    <div class="lp-section" id="lp-middle" style="display:none;"></div>
                    <div class="lp-section" id="lp-bottom">
                        <div class="tab-header">
                            <div class="tab-btn active" onclick="switchLeftTab('jules')"><u>J</u>ules Chat</div>
                            <div class="tab-btn" onclick="switchLeftTab('python')"><u>P</u>ython Code</div>
                        </div>
                        <div class="panel-content" id="jules-content" style="padding:10px; flex: 1; overflow-y: auto;">
                            <div class="msg"><strong>Jules:</strong> Ready to analyze.</div>
                        </div>
                        <div class="panel-content" id="python-content" style="display:none; padding:10px;">
                            <pre style="margin:0; color:#aaa;"># Select a strategy tab to see code</pre>
                        </div>
                        <div class="chat-input-area">
                            <textarea class="chat-input" id="jules-input" placeholder="Ask Jules..."></textarea>
                        </div>
                    </div>
                    <div class="resizer-v" id="resizer-left"></div>
                </div>

                <!-- Main Panel -->
                <div id="main-panel">
                    <div id="chart-workbench">
                        <div class="chart-tabs-bar" id="chart-tabs-bar">
                            <!-- Tabs go here -->
                            <div class="inline-add-container">
                                <input type="text" id="chart-add-input" class="inline-input" placeholder="+ Symbol">
                            </div>
                        </div>
                        <div class="charts-container" id="charts-container">
                            <!-- Chart instances go here -->
                        </div>
                        <div class="resizer-h" id="resizer-charts"></div>
                    </div>

                    <div id="strategy-workbench">
                        <div class="wb-tabs-header">
                            <div class="wb-tab active" data-type="turtle">Turtle Legacy</div>
                            <div class="wb-tab" data-type="statarb">Stat Arb</div>
                        </div>
                        <div class="wb-content" id="wb-content-area">
                            <!-- Dynamic Content Loaded by JS -->
                        </div>
                    </div>
                </div>

                <!-- Toolbox -->
                <div id="toolbox">
                    <div class="toolbox-group" id="strategy-group">
                        <div class="toolbox-item" id="strategies-trigger" title="Strategies">♟️</div>
                        <div class="toolbox-flyout" id="strategies-flyout"></div>
                    </div>
                    <div class="toolbox-item" title="Filters" draggable="true" data-type="filter">🔍</div>
                    <div class="toolbox-item" title="Indicators" draggable="true" data-type="indicator">📊</div>
                    <div class="toolbox-item" title="Risk Models" draggable="true" data-type="risk">🛡️</div>
                </div>
            </div>
        </div>

        <!-- TAB CORPORATE ACTIONS -->
        <div id="tab-corporate_actions" class="main-tab-content">
            <div style="padding: 20px; height: 100%; display: flex; flex-direction: column; box-sizing: border-box;">
                <div style="display: flex; align-items: center; margin-bottom: 15px;">
                    <div class="wb-tabs-header" style="border-bottom: none; display: flex; gap: 10px; flex-wrap: wrap;">
                        <div class="wb-tab active" id="ca-tab-btn-actions" onclick="switchCATab('actions')" style="padding: 6px 15px; border-radius: 4px;">Actions</div>
                        <div class="wb-tab" id="ca-tab-btn-announcements" onclick="switchCATab('announcements')" style="padding: 6px 15px; border-radius: 4px;">Announcements</div>
                        <div class="wb-tab" id="ca-tab-btn-meetings" onclick="switchCATab('meetings')" style="padding: 6px 15px; border-radius: 4px;">Event Calendar</div>
                        <div class="wb-tab" id="ca-tab-btn-rights" onclick="switchCATab('rights')" style="padding: 6px 15px; border-radius: 4px;">Rights</div>
                        <div class="wb-tab" id="ca-tab-btn-ofs" onclick="switchCATab('ofs')" style="padding: 6px 15px; border-radius: 4px;">OFS</div>
                        <div class="wb-tab" id="ca-tab-btn-tender" onclick="switchCATab('tender')" style="padding: 6px 15px; border-radius: 4px;">Tender</div>
                        <div class="wb-tab" id="ca-tab-btn-circulars" onclick="switchCATab('circulars')" style="padding: 6px 15px; border-radius: 4px;">Circulars</div>
                    </div>
                </div>

                <div class="history-controls" style="margin-bottom: 15px; border-radius: 4px; display: flex; flex-direction: column;" id="ca-controls-wrapper">
                    <!-- Issue Status Sub-tabs (Only visible for Rights, OFS, Tender) -->
                    <div id="issue-status-tabs" style="display: none; border-bottom: 1px solid #3f3f46; margin-bottom: 15px;">
                        <button class="status-tab active" data-status="active" onclick="switchIssueStatus('active')" style="background:none;border:none;color:#a1a1aa;padding:8px 16px;cursor:pointer;border-bottom:2px solid transparent;">Active</button>
                        <button class="status-tab" data-status="forthcoming" onclick="switchIssueStatus('forthcoming')" style="background:none;border:none;color:#a1a1aa;padding:8px 16px;cursor:pointer;border-bottom:2px solid transparent;">Forthcoming</button>
                        <button class="status-tab" data-status="past" onclick="switchIssueStatus('past')" style="background:none;border:none;color:#a1a1aa;padding:8px 16px;cursor:pointer;border-bottom:2px solid transparent;">Past</button>
                    </div>
                    <div style="display: flex; gap: 15px; align-items: center;">
                        <div class="control-group">
                            <label>Symbol / Company:</label>
                            <input type="text" id="ca-search-input" class="history-input" placeholder="e.g. RELIANCE" onkeyup="renderCorporateActionsTable()">
                        </div>
                    <div class="control-group" id="ca-actions-filters">
                        <label style="margin-right:10px;">Filter:</label>
                        <label class="checkbox-label" style="margin-right: 10px;"><input type="checkbox" class="ca-filter-cb" value="Dividend" onchange="filterCATable()"> Dividend</label>
                        <label class="checkbox-label" style="margin-right: 10px;"><input type="checkbox" class="ca-filter-cb" value="Bonus" onchange="filterCATable()"> Bonus</label>
                        <label class="checkbox-label" style="margin-right: 10px;"><input type="checkbox" class="ca-filter-cb" value="Split" onchange="filterCATable()"> Split</label>
                        <label class="checkbox-label" style="margin-right: 10px;"><input type="checkbox" class="ca-filter-cb" value="AGM" onchange="filterCATable()"> AGM/EGM</label>
                    </div>
                    <div class="control-group" id="ca-meetings-filters" style="display:none;">
                        <label style="margin-right:10px;">Filter:</label>
                        <label class="checkbox-label" style="margin-right: 10px;"><input type="checkbox" class="ca-filter-cb" value="Financial Results" onchange="filterCATable()"> Financial Results</label>
                        <label class="checkbox-label" style="margin-right: 10px;"><input type="checkbox" class="ca-filter-cb" value="Dividend" onchange="filterCATable()"> Dividend</label>
                        <label class="checkbox-label" style="margin-right: 10px;"><input type="checkbox" class="ca-filter-cb" value="Fund Raising" onchange="filterCATable()"> Fund Raising</label>
                    </div>
                    <div class="control-group" id="ca-public-filters" style="display:none;">
                        <label style="margin-right:10px;">Type:</label>
                        <label class="checkbox-label" style="margin-right: 10px;"><input type="checkbox" class="ca-filter-cb" value="rights" onchange="filterCATable()"> Rights</label>
                        <label class="checkbox-label" style="margin-right: 10px;"><input type="checkbox" class="ca-filter-cb" value="ofs" onchange="filterCATable()"> OFS</label>
                        <label class="checkbox-label" style="margin-right: 10px;"><input type="checkbox" class="ca-filter-cb" value="tender" onchange="filterCATable()"> Tender</label>
                    </div>
                    <button onclick="loadCorporateActionsData()" class="btn btn-primary" id="btn-ca-refresh">Refresh Data</button>
                        <button class="btn btn-secondary" onclick="exportCAData()" style="margin-left: auto;">Export CSV</button>
                    </div>
                </div>

                <div class="table-wrapper" style="flex: 1; border: 1px solid #333; border-radius: 4px;" id="ca-table-container">
                    <table class="data-table" id="ca-main-table">
                        <thead id="ca-main-head"></thead>
                        <tbody id="ca-main-body"></tbody>
                    </table>
                </div>

                <!-- Used specifically for Circulars since it renders differently -->
                <div id="circulars-container" style="display: none; flex: 1; min-height: 0;"></div>

                <div class="history-status-bar" style="border-radius: 0 0 4px 4px;">
                    <span id="ca-status-msg">Ready</span>
                    <span id="ca-row-count">0 Rows</span>
                </div>
            </div>
        </div>

        <!-- TAB DERIVATIVES ANALYSIS -->
        <div id="tab-derivatives" class="main-tab-content">
            <!-- Sub-tab Navigation -->
            <div class="wb-tabs-header" style="background: #1e1e1e; padding: 10px 20px 0 20px; border-bottom: 1px solid #333; display: flex; gap: 15px;">
                <div class="wb-tab active" id="deriv-tab-btn-matrix" onclick="switchDerivTab('matrix')" style="padding: 8px 15px; cursor: pointer; border-bottom: 2px solid transparent;">Data Matrix</div>
                <div class="wb-tab" id="deriv-tab-btn-oi" onclick="switchDerivTab('oi')" style="padding: 8px 15px; cursor: pointer; border-bottom: 2px solid transparent;">OI Analysis</div>
                <div class="wb-tab" id="deriv-tab-btn-rollover" onclick="switchDerivTab('rollover')" style="padding: 8px 15px; cursor: pointer; border-bottom: 2px solid transparent;">Rollover Analysis</div>
                <div class="wb-tab" id="deriv-tab-btn-market" onclick="switchDerivTab('market')" style="padding: 8px 15px; cursor: pointer; border-bottom: 2px solid transparent;">Market Activity</div>
            </div>

            <!-- Sub-tab Contents Container -->
            <div style="position: relative; flex: 1; height: calc(100% - 45px); overflow: hidden; display: flex; flex-direction: row; width: 100%;">

                <!-- SUB-TAB 1: Data Matrix (Original Reports View) -->
                <div id="deriv-tab-matrix" class="deriv-sub-tab active" style="display: flex; height: 100%; width: 100%;">

                <!-- Left Panel: Controls & Archive -->
                <div style="width: 300px; background: #252526; border-right: 1px solid #333; display: flex; flex-direction: column; flex-shrink: 0;">

                    <div style="padding: 20px; border-bottom: 1px solid #333;">
                        <h2 style="margin: 0 0 5px 0; font-size: 16px; color: #fff;">Data Matrix</h2>
                        <p style="margin: 0 0 20px 0; font-size: 12px; color: #888;">Synthesize daily PDF reports.</p>

                        <div style="display: flex; gap: 10px; margin-bottom: 15px;">
                            <div class="control-group" style="flex: 1; flex-direction: column; align-items: flex-start;">
                                <label for="mr-target-date" style="color:#ccc; margin-bottom: 5px; font-size: 11px;">From Date</label>
                                <input type="date" id="mr-target-date" class="history-input" style="width: 100%; box-sizing: border-box; padding: 4px;">
                            </div>
                            <div class="control-group" style="flex: 1; flex-direction: column; align-items: flex-start;">
                                <label for="mr-end-date" style="color:#ccc; margin-bottom: 5px; font-size: 11px;">To Date (Optional)</label>
                                <input type="date" id="mr-end-date" class="history-input" style="width: 100%; box-sizing: border-box; padding: 4px;">
                            </div>
                        </div>

                        <div class="control-group" style="margin-bottom: 20px; flex-direction: column; align-items: flex-start;">
                            <label for="mr-author-name" style="color:#ccc; margin-bottom: 5px; font-size: 11px;">Analyst / Author</label>
                            <input type="text" id="mr-author-name" class="history-input" value="Turtle Terminal Quant System" style="width: 100%; box-sizing: border-box;">
                        </div>

                        <button id="mr-prepare-btn" class="btn btn-secondary" style="width: 100%; margin-bottom: 10px; padding: 8px; border: 1px solid #555;">1. Prepare Data</button>
                        <button id="mr-generate-btn" class="btn btn-primary" style="margin-left: auto;" disabled>2. Generate PDF Report</button>



                        <div id="mr-status-text" style="color: #aaa; margin-top: 15px; font-size: 12px; font-style: italic; text-align: center;"></div>
                        <button id="mr-download-btn" class="btn" style="width: 100%; padding: 8px; background-color: #28a745; display: none; margin-top: 10px; color: white; border: none;">Open PDF</button>
                    </div>

                    <div style="flex: 1; padding: 20px; overflow-y: auto;">
                        <h3 style="margin: 0 0 10px 0; font-size: 14px; color: #ccc; border-bottom: 1px solid #444; padding-bottom: 5px;">Report Archive</h3>
                        <ul id="mr-archive-list" style="list-style: none; padding: 0; margin: 0; font-size: 13px;">
                            <li style="color: #666; font-style: italic;">Loading archive...</li>
                        </ul>
                    </div>

                </div>

                <!-- Right Panel: Data View Area -->
                <div style="flex: 1; display: flex; flex-direction: column; background: #1e1e1e; max-width: calc(100vw - 300px);">
                    <!-- Data Grid Controls -->
                    <div style="padding: 10px; background: #252526; border-bottom: 1px solid #333; display: flex; gap: 10px; align-items: center;">
                        <span style="color: #aaa; font-size: 13px;">Symbol Timeseries:</span>
                        <input type="text" id="mr-symbol-input" class="history-input" placeholder="e.g. NIFTY" style="width: 150px;" value="NIFTY">
                        <button id="mr-fetch-ts-btn" class="btn btn-secondary" style="padding: 4px 10px;">Load Timeseries</button>
                        <button id="mr-clear-ts-btn" class="btn btn-secondary" style="padding: 4px 10px; margin-left: 5px;">Clear (All Scrips)</button>
                        <button id="mr-export-btn" class="btn btn-secondary" style="padding: 4px 10px; margin-left: 10px;">Download CSV</button>
                    </div>

                    <div class="table-wrapper" style="flex: 1; min-height: 0; border-radius: 0; margin: 0; overflow-x: auto; max-width: 100%;">
                        <table class="data-table" id="mr-data-table">
                            <thead id="mr-data-head">
                                <tr>
                                    <th style="text-align: left; position: sticky; top: 0; left: 0; background: #1e1e1e; z-index: 3; min-width: 90px; max-width: 90px; width: 90px;">Date</th>
                                    <th style="text-align: left; position: sticky; top: 0; left: 0; background: #1e1e1e; z-index: 3; min-width: 90px; max-width: 90px; width: 90px;">Symbol</th>
                                    <th style="white-space: pre-wrap;">Near Fut<br>Close</th>
                                    <th style="white-space: pre-wrap;">EQ<br>Close</th>
                                    <th style="white-space: pre-wrap;">VWAP</th>
                                    <th style="white-space: pre-wrap;">Futures<br>Total Vol</th>
                                    <th style="white-space: pre-wrap;">Futures<br>Total OI</th>
                                    <th style="white-space: pre-wrap;">Put-Call<br>Ratio (OI)</th>
                                    <th style="white-space: pre-wrap;">Highest OI<br>Strike (PE)</th>
                                    <th style="white-space: pre-wrap;">% Away<br>(PE)</th>
                                    <th style="white-space: pre-wrap;">Highest OI<br>Value (PE)</th>
                                    <th style="white-space: pre-wrap;">Highest OI<br>Strike (CE)</th>
                                    <th style="white-space: pre-wrap;">% Away<br>(CE)</th>
                                    <th style="white-space: pre-wrap;">Highest OI<br>Value (CE)</th>
                                    <th style="white-space: pre-wrap;">ATM Straddle<br>(Near Month)</th>
                                    <th style="white-space: pre-wrap;">ATM Straddle<br>(Weekly NIFTY)</th>
                                    <th style="white-space: pre-wrap;">Change in OI<br>(Options)</th>
                                    <th style="white-space: pre-wrap;">Change in OI<br>(Futures)</th>
                                    <th style="white-space: pre-wrap;">Fut 1<br>Expiry</th>
                                    <th style="white-space: pre-wrap;">Fut 2<br>Expiry</th>
                                    <th style="white-space: pre-wrap;">Fut 3<br>Expiry</th>
                                    <th style="white-space: pre-wrap;">Total Options<br>Call OI</th>
                                    <th style="white-space: pre-wrap;">Total Options<br>Put OI</th>
                                    <th style="white-space: pre-wrap;">ATM IV<br>(Near)</th>
                                    <th style="white-space: pre-wrap;">ATM IV<br>(Next)</th>
                                    <th style="white-space: pre-wrap;">IV Rank<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">IV Percentile<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">25-Delta Skew<br>(Near)</th>
                                    <th style="white-space: pre-wrap;">25-Delta Skew<br>(Far)</th>
                                    <th style="white-space: pre-wrap;">1-Sigma Daily<br>Volatility</th>
                                    <th style="white-space: pre-wrap;">Rollover<br>Percentage</th>

                                    <th style="white-space: pre-wrap;">Basis 1<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">Basis 2<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">Calendar Spread 1<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">Calendar Spread 2<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">P/E<br>Ratio</th>
                                    <th style="white-space: pre-wrap;">&beta;<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">&beta;<br>(500d)</th>
                                    <th style="white-space: pre-wrap;">R-Squared<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">R-Squared<br>(500d)</th>
                                    <th style="white-space: pre-wrap;">Price %<br>Change</th>
                                    <th style="white-space: pre-wrap;">Relative Vol<br>(20d)</th>
                                    <th style="white-space: pre-wrap;">14-Day<br>ATR %</th>
                                    <th style="white-space: pre-wrap;">20-Day<br>EMA</th>
                                    <th style="white-space: pre-wrap;">50-Day<br>EMA</th>
                                    <th style="white-space: pre-wrap;">100-Day<br>EMA</th>
                                    <th style="white-space: pre-wrap;">200-Day<br>EMA</th>
                                </tr>
                            </thead>
                            <tbody id="mr-data-body">
                                <tr><td colspan="47" style="text-align: center; color: #666; padding: 20px;">Enter a symbol, then click 'Load Timeseries' to view historical data.</td></tr>
                            </tbody>
                            </table>
                        </div>
                    </div>
                </div>

            </div>
// script start
                document.getElementById('mr-target-date').valueAsDate = new Date();
                let mrPollingInterval;

                // Load Archive
                async function loadMrArchive() {
                    const list = document.getElementById('mr-archive-list');
                    try {
                        const res = await fetch('/api/morning-report/list');
                        const data = await res.json();
                        if (data.reports.length === 0) {
                            list.innerHTML = '<li style="color: #666; font-style: italic;">No reports found.</li>';
                            return;
                        }
                        list.innerHTML = '';
                        data.reports.forEach(r => {
                            const li = document.createElement('li');
                            li.style.marginBottom = '8px';
                            li.innerHTML = `<a href="${r.url}" target="_blank" style="color: #4da6ff; text-decoration: none;">📄 ${r.date}</a>`;
                            list.appendChild(li);
                        });
                    } catch (e) {
                        list.innerHTML = '<li style="color: red;">Failed to load.</li>';
                    }
                }

                // Initialize archive list
                loadMrArchive();

                // Prepare Data Button Handler
                document.getElementById('mr-prepare-btn').addEventListener('click', async () => {
                    const targetDate = document.getElementById('mr-target-date').value;
                    const endDate = document.getElementById('mr-end-date').value;
                    const statusText = document.getElementById('mr-status-text');
                    const prepBtn = document.getElementById('mr-prepare-btn');
                    const genBtn = document.getElementById('mr-generate-btn');
                    const tbody = document.getElementById('mr-data-body');

                    if(!targetDate) { alert('Please select a From Date.'); return; }

                    prepBtn.disabled = true;
                    prepBtn.style.opacity = '0.5';
                    statusText.innerText = endDate ? 'Triggering historical range preparation task (this may take a while)...' : 'Triggering data preparation task...';
                    statusText.style.color = '#aaa';
                    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #888; padding: 20px;">Calculating composite metrics...</td></tr>';

                    try {
                        const res = await fetch('/api/morning-report/prepare', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ target_date: targetDate, end_date: endDate || null })
                        });
                        const data = await res.json();

                        if(data.task_id) {
                            statusText.innerText = 'Processing metrics...';
                            mrPollingInterval = setInterval(() => checkPrepStatus(data.task_id, targetDate), 3000);
                        } else {
                            throw new Error('No task ID returned.');
                        }
                    } catch (e) {
                        statusText.innerText = `Error: ${e.message}`;
                        statusText.style.color = 'red';
                        prepBtn.disabled = false;
                        prepBtn.style.opacity = '1';
                    }
                });

                async function checkPrepStatus(taskId, targetDate) {
                    try {
                        const res = await fetch(`/api/morning-report/status/${taskId}`);
                        const data = await res.json();
                        const statusText = document.getElementById('mr-status-text');
                        const genBtn = document.getElementById('mr-generate-btn');
                        const prepBtn = document.getElementById('mr-prepare-btn');

                        if(data.state === 'SUCCESS' || data.status === 'SUCCESS') {
                            clearInterval(mrPollingInterval);
                            statusText.innerText = 'Data Prepared Successfully.';
                            statusText.style.color = '#28a745';

                            prepBtn.disabled = false;
                            prepBtn.style.opacity = '1';
                            genBtn.disabled = false;
                            genBtn.style.opacity = '1';

                            // Auto-load data
                            loadTimeseriesData(true);
                        } else if(data.state === 'FAILURE' || data.status === 'FAILED' || data.status === 'FAILURE') {
                            clearInterval(mrPollingInterval);
                            statusText.innerText = `Preparation Failed: ${data.error || 'Unknown Error'}`;
                            statusText.style.color = 'red';
                            prepBtn.disabled = false;
                            prepBtn.style.opacity = '1';
                        }
                    } catch (e) {
                        console.error('Error polling prep status', e);
                    }
                }

                // View Data Button Handler (Timeseries / Snapshot)
                const generateTableHTML = (row, isSnapshot) => {
                            const close = (row.close_price != null && !isNaN(Number(row.close_price))) ? Number(row.close_price).toFixed(2) : '-';
                            const eqClose = (row.eq_close_price != null && !isNaN(Number(row.eq_close_price))) ? Number(row.eq_close_price).toFixed(2) : '-';
                            const vwap = (row.vwap != null && !isNaN(Number(row.vwap))) ? Number(row.vwap).toFixed(2) : '-';
                            const eqVol = (row.total_eq_volume != null && !isNaN(Number(row.total_eq_volume))) ? Number(row.total_eq_volume).toLocaleString() : '-';
                            const delPct = (row.delivery_pct != null && !isNaN(Number(row.delivery_pct))) ? Number(row.delivery_pct).toFixed(2) : '-';
                            const fVol = (row.futures_total_vol != null && !isNaN(Number(row.futures_total_vol))) ? Number(row.futures_total_vol).toLocaleString() : '-';
                            const fOi = (row.futures_total_oi != null && !isNaN(Number(row.futures_total_oi))) ? Number(row.futures_total_oi).toLocaleString() : '-';
                            const pcr = (row.pcr_oi != null && !isNaN(Number(row.pcr_oi))) ? Number(row.pcr_oi).toFixed(2) : '-';

                            const hiOiStrikePe = (row.highest_oi_strike_pe != null && !isNaN(Number(row.highest_oi_strike_pe))) ? Number(row.highest_oi_strike_pe).toLocaleString() : '-';
                            const pctAwayPe = (row.pct_away_highest_pe != null && !isNaN(Number(row.pct_away_highest_pe))) ? (Number(row.pct_away_highest_pe)).toFixed(2) + '%' : '-';
                            const hiOiStrikeCe = (row.highest_oi_strike_ce != null && !isNaN(Number(row.highest_oi_strike_ce))) ? Number(row.highest_oi_strike_ce).toLocaleString() : '-';
                            const pctAwayCe = (row.pct_away_highest_ce != null && !isNaN(Number(row.pct_away_highest_ce))) ? (Number(row.pct_away_highest_ce)).toFixed(2) + '%' : '-';
                            const hiOiPeValue = (row.highest_oi_pe_value != null && !isNaN(Number(row.highest_oi_pe_value))) ? Number(row.highest_oi_pe_value).toFixed(2) : '-';
                            const hiOiCeValue = (row.highest_oi_ce_value != null && !isNaN(Number(row.highest_oi_ce_value))) ? Number(row.highest_oi_ce_value).toFixed(2) : '-';
                            const hiOiPeOi = (row.highest_oi_pe_oi != null && !isNaN(Number(row.highest_oi_pe_oi))) ? Number(row.highest_oi_pe_oi).toLocaleString() : '-';
                            const hiOiCeOi = (row.highest_oi_ce_oi != null && !isNaN(Number(row.highest_oi_ce_oi))) ? Number(row.highest_oi_ce_oi).toLocaleString() : '-';
                            const atmStraddleNear = (row.atm_straddle_near_month != null && !isNaN(Number(row.atm_straddle_near_month))) ? Number(row.atm_straddle_near_month).toFixed(2) : '-';
                            const atmStraddleWeekly = (row.atm_straddle_weekly_nifty != null && !isNaN(Number(row.atm_straddle_weekly_nifty))) ? Number(row.atm_straddle_weekly_nifty).toFixed(2) : '-';
                            const chgOiOpt = (row.chg_oi_options != null && !isNaN(Number(row.chg_oi_options))) ? Number(row.chg_oi_options).toLocaleString() : '-';
                            const chgOiFut = (row.chg_oi_futures != null && !isNaN(Number(row.chg_oi_futures))) ? Number(row.chg_oi_futures).toLocaleString() : '-';
                            const fut1Exp = row.near_expiry_date !== null ? row.near_expiry_date : '-';
                            const fut2Exp = row.next_expiry_date !== null ? row.next_expiry_date : '-';
                            const fut3Exp = row.far_expiry_date !== null ? row.far_expiry_date : '-';
                            const totCallOi = (row.total_options_call_oi != null && !isNaN(Number(row.total_options_call_oi))) ? Number(row.total_options_call_oi).toLocaleString() : '-';
                            const totPutOi = (row.total_options_put_oi != null && !isNaN(Number(row.total_options_put_oi))) ? Number(row.total_options_put_oi).toLocaleString() : '-';

                            const atmIvNear = (row.atm_iv_near != null && !isNaN(Number(row.atm_iv_near))) ? (Number(row.atm_iv_near) * 100).toFixed(2) + '%' : '-';
                            const atmIvNext = (row.atm_iv_next != null && !isNaN(Number(row.atm_iv_next))) ? (Number(row.atm_iv_next) * 100).toFixed(2) + '%' : '-';
                            const ivRank = (row.iv_rank_252 != null && !isNaN(Number(row.iv_rank_252))) ? Number(row.iv_rank_252).toFixed(2) : '-';
                            const ivPctile = (row.iv_percentile_252 != null && !isNaN(Number(row.iv_percentile_252))) ? Number(row.iv_percentile_252).toFixed(2) : '-';
                            const skewNear = (row.skew_25d_near != null && !isNaN(Number(row.skew_25d_near))) ? (Number(row.skew_25d_near) * 100).toFixed(2) + '%' : '-';
                            const skewFar = (row.skew_25d_far != null && !isNaN(Number(row.skew_25d_far))) ? (Number(row.skew_25d_far) * 100).toFixed(2) + '%' : '-';
                            const vol1Sig = (row.daily_volatility != null && !isNaN(Number(row.daily_volatility))) ? (Number(row.daily_volatility) * 100).toFixed(2) + '%' : '-';

                            const roll = (row.rollover_pct != null && !isNaN(Number(row.rollover_pct))) ? (Number(row.rollover_pct) * 100).toFixed(2) + '%' : '-';

                            let mwpl = '0.00';
                            let maxMwpl = 0;
                            let maxClient = '';
                            if (row.mwpl_array && Array.isArray(row.mwpl_array) && row.mwpl_array.length > 0) {
                                // mwpl_array is usually [{"client_name": value}, ...] or [value] or string.
                                // To be safe, we extract the highest value if it's an array of objects.
                                try {
                                    row.mwpl_array.forEach(item => {
                                        if (typeof item === 'object' && item !== null) {
                                            for (let key in item) {
                                                const val = parseFloat(item[key]);
                                                if (!isNaN(val) && val > maxMwpl) {
                                                    maxMwpl = val;
                                                    maxClient = key;
                                                }
                                            }
                                        } else if (typeof item === 'number') {
                                            if (item > maxMwpl) maxMwpl = item;
                                        }
                                    });
                                    if (maxMwpl > 0) {
                                        mwpl = maxMwpl.toFixed(2);
                                    } else {
                                        // fallback if structure was different
                                        const firstKey = Object.keys(row.mwpl_array[0])[0];
                                        if (firstKey) mwpl = parseFloat(row.mwpl_array[0][firstKey]).toFixed(2);
                                    }
                                } catch (e) {
                                    mwpl = '0.00';
                                }
                            }

                            const basis1 = (row.basis_1_bps != null && !isNaN(Number(row.basis_1_bps))) ? Number(row.basis_1_bps).toFixed(0) : '-';
                            const basis2 = (row.basis_2_bps != null && !isNaN(Number(row.basis_2_bps))) ? Number(row.basis_2_bps).toFixed(0) : '-';
                            const cal1 = (row.calendar_spread_1_bps != null && !isNaN(Number(row.calendar_spread_1_bps))) ? Number(row.calendar_spread_1_bps).toFixed(0) : '-';
                            const cal2 = (row.calendar_spread_2_bps != null && !isNaN(Number(row.calendar_spread_2_bps))) ? Number(row.calendar_spread_2_bps).toFixed(0) : '-';

                            const pe = (row.pe_ratio != null && !isNaN(Number(row.pe_ratio))) ? Number(row.pe_ratio).toFixed(2) : '-';
                            const b252 = (row.beta_252 != null && !isNaN(Number(row.beta_252))) ? Number(row.beta_252).toFixed(2) : '-';
                            const b500 = (row.beta_500 != null && !isNaN(Number(row.beta_500))) ? Number(row.beta_500).toFixed(2) : '-';
                            const r252 = (row.r_squared_252 != null && !isNaN(Number(row.r_squared_252))) ? Number(row.r_squared_252).toFixed(2) : '-';
                            const r500 = (row.r_squared_500 != null && !isNaN(Number(row.r_squared_500))) ? Number(row.r_squared_500).toFixed(2) : '-';
                            const pxPct = (row.price_pct_change != null && !isNaN(Number(row.price_pct_change))) ? (Number(row.price_pct_change)).toFixed(2) + '%' : '-';
                            const relVol = (row.relative_volume_20d != null && !isNaN(Number(row.relative_volume_20d))) ? Number(row.relative_volume_20d).toFixed(2) : '-';

                            const atr = (row.atr_14_cash != null && !isNaN(Number(row.atr_14_cash))) ? Number(row.atr_14_cash).toFixed(2) : '-';
                            const ema20 = (row.ema_20_cash != null && !isNaN(Number(row.ema_20_cash))) ? Number(row.ema_20_cash).toFixed(2) : '-';
                            const ema50 = (row.ema_50_cash != null && !isNaN(Number(row.ema_50_cash))) ? Number(row.ema_50_cash).toFixed(2) : '-';
                            const ema100 = (row.ema_100_cash != null && !isNaN(Number(row.ema_100_cash))) ? Number(row.ema_100_cash).toFixed(2) : '-';
                            const ema200 = (row.ema_200_cash != null && !isNaN(Number(row.ema_200_cash))) ? Number(row.ema_200_cash).toFixed(2) : '-';

                            // Note: delivery fields don't exist in model, using '-'
                            const del5 = '-';
                            const del10 = '-';
                            const del20 = '-';
                            const del30 = '-';

                            let html = ``;
                            if(!isSnapshot) {
                                html += `<td style="position: sticky; left: 0; background: #1e1e1e; z-index: 2;">${row.trade_date}</td>`;
                                html += `<td style="position: sticky; left: 90px; background: #1e1e1e; z-index: 2;">${row.symbol}</td>`;
                            } else {
                                html += `<td style="position: sticky; left: 0; background: #1e1e1e; z-index: 2;">${row.symbol}</td>`;
                            }

                            html += `
                                <td>${close}</td>
                                <td>${eqClose}</td>
                                <td>${vwap}</td>
                                <td>${eqVol}</td>
                                <td>${delPct}</td>
                                <td>${fVol}</td>
                                <td>${fOi}</td>
                                <td>${pcr}</td>
                                <td>${hiOiStrikePe}</td>
                                <td>${pctAwayPe}</td>
                                <td>${hiOiPeOi}</td>
                                <td>${hiOiPeValue}</td>
                                <td>${hiOiStrikeCe}</td>
                                <td>${pctAwayCe}</td>
                                <td>${hiOiCeOi}</td>
                                <td>${hiOiCeValue}</td>
                                <td>${atmStraddleNear}</td>
                                <td>${atmStraddleWeekly}</td>
                                <td>${chgOiOpt}</td>
                                <td>${chgOiFut}</td>
                                <td>${fut1Exp}</td>
                                <td>${fut2Exp}</td>
                                <td>${fut3Exp}</td>
                                <td>${totCallOi}</td>
                                <td>${totPutOi}</td>
                                <td>${atmIvNear}</td>
                                <td>${atmIvNext}</td>
                                <td>${ivRank}</td>
                                <td>${ivPctile}</td>
                                <td>${skewNear}</td>
                                <td>${skewFar}</td>
                                <td>${vol1Sig}</td>
                                <td>${roll}</td>
                                <td style="color: ${parseFloat(mwpl) > 20 ? '#ff4d4d' : 'inherit'};">${mwpl}</td>
                                <td>${basis1}</td>
                                <td>${basis2}</td>
                                <td>${cal1}</td>
                                <td>${cal2}</td>
                                <td>${pe}</td>
                                <td>${b252}</td>
                                <td>${b500}</td>
                                <td>${r252}</td>
                                <td>${r500}</td>
                                <td>${pxPct}</td>
                                <td>${relVol}</td>
                                <td>${atr}</td>
                                <td>${ema20}</td>
                                <td>${ema50}</td>
                                <td>${ema100}</td>
                                <td>${ema200}</td>
                            </tr>
                        \`;
                        return html;
                }

                async function loadTimeseriesData(snapshotMode = true) {
                    const targetDate = document.getElementById('mr-target-date').value;
                    const symbol = document.getElementById('mr-symbol-input').value.toUpperCase() || 'NIFTY';
                    const tbody = document.getElementById('mr-data-body');
                    const thead = document.getElementById('mr-data-head');
                    const statusText = document.getElementById('mr-status-text');

                    if(snapshotMode && !targetDate) return;
                    if(!snapshotMode && !symbol) { alert('Please enter a symbol for Timeseries view.'); return; }

                    try {
                        let url = `/api/morning-report/data/${targetDate}`;
                        if (!snapshotMode) {
                            url = `/api/morning-report/timeseries?symbol=${symbol}`;
                        }

                        const res = await fetch(url);
                        if (!res.ok) throw new Error('Data fetch failed');
                        const data = await res.json();

                        tbody.innerHTML = '';
                        if(data.length === 0) {
                            tbody.innerHTML = `<tr><td colspan="${snapshotMode ? 51 : 52}" style="text-align: center; color: #888; padding: 20px;">No data found.</td></tr>`;
                            return;
                        }

                        if (snapshotMode) {
                            thead.innerHTML = `
                                <tr>
                                    <th style="text-align: left; position: sticky; top: 0; left: 0; background: #1e1e1e; z-index: 3; min-width: 90px; max-width: 90px; width: 90px;">Date</th>
                                    <th style="text-align: left; position: sticky; top: 0; left: 90px; background: #1e1e1e; z-index: 3; min-width: 90px; max-width: 90px; width: 90px;">Symbol</th>
                                    <th style="white-space: pre-wrap;">Near Fut<br>Close</th>
                                    <th style="white-space: pre-wrap;">EQ<br>Close</th>
                                    <th style="white-space: pre-wrap;">VWAP</th>
                                    <th style="white-space: pre-wrap;">Total EQ<br>Volume</th>
                                    <th style="white-space: pre-wrap;">Delivery<br>(%)</th>
                                    <th style="white-space: pre-wrap;">Futures<br>Total Vol</th>
                                    <th style="white-space: pre-wrap;">Futures<br>Total OI</th>
                                    <th style="white-space: pre-wrap;">Put-Call<br>Ratio (OI)</th>
                                    <th style="white-space: pre-wrap;">Highest OI<br>Strike (PE)</th>
                                    <th style="white-space: pre-wrap;">% Away<br>(PE)</th>
                                    <th style="white-space: pre-wrap;">Highest OI<br>(PE)</th>
                                    <th style="white-space: pre-wrap;">Highest OI<br>Value (PE)</th>
                                    <th style="white-space: pre-wrap;">Highest OI<br>Strike (CE)</th>
                                    <th style="white-space: pre-wrap;">% Away<br>(CE)</th>
                                    <th style="white-space: pre-wrap;">Highest OI<br>(CE)</th>
                                    <th style="white-space: pre-wrap;">Highest OI<br>Value (CE)</th>
                                    <th style="white-space: pre-wrap;">ATM Straddle<br>(Near Month)</th>
                                    <th style="white-space: pre-wrap;">ATM Straddle<br>(Weekly NIFTY)</th>
                                    <th style="white-space: pre-wrap;">Change in OI<br>(Options)</th>
                                    <th style="white-space: pre-wrap;">Change in OI<br>(Futures)</th>
                                    <th style="white-space: pre-wrap;">Fut 1<br>Expiry</th>
                                    <th style="white-space: pre-wrap;">Fut 2<br>Expiry</th>
                                    <th style="white-space: pre-wrap;">Fut 3<br>Expiry</th>
                                    <th style="white-space: pre-wrap;">Total Options<br>Call OI</th>
                                    <th style="white-space: pre-wrap;">Total Options<br>Put OI</th>
                                    <th style="white-space: pre-wrap;">ATM IV<br>(Near)</th>
                                    <th style="white-space: pre-wrap;">ATM IV<br>(Next)</th>
                                    <th style="white-space: pre-wrap;">IV Rank<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">IV Percentile<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">25-Delta Skew<br>(Near)</th>
                                    <th style="white-space: pre-wrap;">25-Delta Skew<br>(Far)</th>
                                    <th style="white-space: pre-wrap;">1-Sigma Daily<br>Volatility</th>
                                    <th style="white-space: pre-wrap;">Rollover<br>Percentage</th>

                                    <th style="white-space: pre-wrap;">Basis 1<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">Basis 2<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">Calendar Spread 1<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">Calendar Spread 2<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">P/E<br>Ratio</th>
                                    <th style="white-space: pre-wrap;">&beta;<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">&beta;<br>(500d)</th>
                                    <th style="white-space: pre-wrap;">R-Squared<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">R-Squared<br>(500d)</th>
                                    <th style="white-space: pre-wrap;">Price %<br>Change</th>
                                    <th style="white-space: pre-wrap;">Relative Vol<br>(20d)</th>
                                    <th style="white-space: pre-wrap;">14-Day<br>ATR %</th>
                                    <th style="white-space: pre-wrap;">20-Day<br>EMA</th>
                                    <th style="white-space: pre-wrap;">50-Day<br>EMA</th>
                                    <th style="white-space: pre-wrap;">100-Day<br>EMA</th>
                                    <th style="white-space: pre-wrap;">200-Day<br>EMA</th>
                                </tr>
                            `;
                            const renderChunk = (start) => {
                                const end = Math.min(start + 50, data.length);
                                const fragment = document.createDocumentFragment();
                                for (let i = start; i < end; i++) {
                                    const tr = document.createElement('tr');
                                    tr.innerHTML = generateTableHTML(data[i], true);
                                    fragment.appendChild(tr);
                                }
                                tbody.appendChild(fragment);
                                if (end < data.length) {
                                    requestAnimationFrame(() => renderChunk(end));
                                } else {
                                    statusText.innerText = `Loaded ${data.length} records.`;
                                    const genBtn = document.getElementById('mr-generate-btn');
                                    if(genBtn) { genBtn.disabled = false; genBtn.style.opacity = '1'; }
                                }
                            };
                            requestAnimationFrame(() => renderChunk(0));
                        } else {
                            thead.innerHTML = `
                                <tr>
                                    <th style="text-align: left; position: sticky; top: 0; left: 0; background: #1e1e1e; z-index: 3; min-width: 90px; max-width: 90px; width: 90px;">Date</th>
                                    <th style="text-align: left; position: sticky; top: 0; left: 90px; background: #1e1e1e; z-index: 3; min-width: 90px; max-width: 90px; width: 90px;">Symbol</th>
                                    <th style="white-space: pre-wrap;">Near Fut<br>Close</th>
                                    <th style="white-space: pre-wrap;">EQ<br>Close</th>
                                    <th style="white-space: pre-wrap;">VWAP</th>
                                    <th style="white-space: pre-wrap;">Futures<br>Total Vol</th>
                                    <th style="white-space: pre-wrap;">Futures<br>Total OI</th>
                                    <th style="white-space: pre-wrap;">Put-Call<br>Ratio (OI)</th>
                                    <th style="white-space: pre-wrap;">Highest OI<br>Strike (PE)</th>
                                    <th style="white-space: pre-wrap;">% Away<br>(PE)</th>
                                    <th style="white-space: pre-wrap;">Highest OI<br>Value (PE)</th>
                                    <th style="white-space: pre-wrap;">Highest OI<br>Strike (CE)</th>
                                    <th style="white-space: pre-wrap;">% Away<br>(CE)</th>
                                    <th style="white-space: pre-wrap;">Highest OI<br>Value (CE)</th>
                                    <th style="white-space: pre-wrap;">ATM Straddle<br>(Near Month)</th>
                                    <th style="white-space: pre-wrap;">ATM Straddle<br>(Weekly NIFTY)</th>
                                    <th style="white-space: pre-wrap;">Change in OI<br>(Options)</th>
                                    <th style="white-space: pre-wrap;">Change in OI<br>(Futures)</th>
                                    <th style="white-space: pre-wrap;">Fut 1<br>Expiry</th>
                                    <th style="white-space: pre-wrap;">Fut 2<br>Expiry</th>
                                    <th style="white-space: pre-wrap;">Fut 3<br>Expiry</th>
                                    <th style="white-space: pre-wrap;">Total Options<br>Call OI</th>
                                    <th style="white-space: pre-wrap;">Total Options<br>Put OI</th>
                                    <th style="white-space: pre-wrap;">ATM IV<br>(Near)</th>
                                    <th style="white-space: pre-wrap;">ATM IV<br>(Next)</th>
                                    <th style="white-space: pre-wrap;">IV Rank<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">IV Percentile<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">25-Delta Skew<br>(Near)</th>
                                    <th style="white-space: pre-wrap;">25-Delta Skew<br>(Far)</th>
                                    <th style="white-space: pre-wrap;">1-Sigma Daily<br>Volatility</th>
                                    <th style="white-space: pre-wrap;">Rollover<br>Percentage</th>

                                    <th style="white-space: pre-wrap;">Basis 1<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">Basis 2<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">Calendar Spread 1<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">Calendar Spread 2<br>(bps)</th>
                                    <th style="white-space: pre-wrap;">P/E<br>Ratio</th>
                                    <th style="white-space: pre-wrap;">&beta;<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">&beta;<br>(500d)</th>
                                    <th style="white-space: pre-wrap;">R-Squared<br>(252d)</th>
                                    <th style="white-space: pre-wrap;">R-Squared<br>(500d)</th>
                                    <th style="white-space: pre-wrap;">Price %<br>Change</th>
                                    <th style="white-space: pre-wrap;">Relative Vol<br>(20d)</th>
                                    <th style="white-space: pre-wrap;">14-Day<br>ATR %</th>
                                    <th style="white-space: pre-wrap;">20-Day<br>EMA</th>
                                    <th style="white-space: pre-wrap;">50-Day<br>EMA</th>
                                    <th style="white-space: pre-wrap;">100-Day<br>EMA</th>
                                    <th style="white-space: pre-wrap;">200-Day<br>EMA</th>
                                </tr>
                            `;
                            const renderChunk = (start) => {
                                const end = Math.min(start + 50, data.length);
                                const fragment = document.createDocumentFragment();
                                for (let i = start; i < end; i++) {
                                    const tr = document.createElement('tr');
                                    tr.innerHTML = generateTableHTML(data[i], false);
                                    fragment.appendChild(tr);
                                }
                                tbody.appendChild(fragment);
                                if (end < data.length) {
                                    requestAnimationFrame(() => renderChunk(end));
                                } else {
                                    statusText.innerText = `Loaded ${data.length} records.`;
                                }
                            };
                            requestAnimationFrame(() => renderChunk(0));
                        }
                    } catch(e) {
                        statusText.innerText = 'Failed to load data.';
                        tbody.innerHTML = `<tr><td colspan="47" style="text-align: center; color: red; padding: 20px;">${e.message}</td></tr>`;
                    }
                }

                document.getElementById('mr-fetch-ts-btn').addEventListener('click', () => loadTimeseriesData(false));

                document.getElementById('mr-clear-ts-btn').addEventListener('click', () => {
                    document.getElementById('mr-symbol-input').value = '';
                    loadTimeseriesData(true);
                });

                document.getElementById('mr-export-btn').addEventListener('click', async () => {
                    const btn = document.getElementById('mr-export-btn');
                    const originalText = btn.innerText;
                    btn.disabled = true;
                    btn.innerHTML = '⏳ Downloading...';

                    try {
                        const thead = document.getElementById('mr-data-head');
                        const tbody = document.getElementById('mr-data-body');

                        if (tbody.rows.length === 0 || tbody.innerText.includes('Loading') || tbody.innerText.includes('No data')) {
                            alert("No data to export.");
                            return;
                        }

                        let csv = [];
                        const headers = Array.from(thead.querySelectorAll('th')).map(th => `"${th.innerText.replace(/\n/g, ' ').replace(/"/g, '""').trim()}"`);
                        csv.push(headers.join(","));

                        Array.from(tbody.querySelectorAll('tr')).forEach(tr => {
                            const row = Array.from(tr.querySelectorAll('td')).map(td => `"${td.innerText.replace(/"/g, '""').trim()}"`);
                            csv.push(row.join(","));
                        });

                        const blob = new Blob([csv.join("\n")], { type: 'text/csv' });
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.setAttribute('hidden', '');
                        a.setAttribute('href', url);

                        const isSnapshot = thead.querySelectorAll('th')[0].innerText.includes('Symbol');
                        let filename = 'Derivatives_Analysis';
                        if (isSnapshot) {
                            const targetDate = document.getElementById('mr-target-date').value || new Date().toISOString().slice(0,10);
                            filename = `Derivatives_Analysis_Snapshot_${targetDate}`;
                        } else {
                            const symbol = document.getElementById('mr-symbol-input').value.toUpperCase() || 'NIFTY';
                            filename = `Derivatives_Analysis_Timeseries_${symbol}`;
                        }

                        a.setAttribute('download', `${filename}.csv`);
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                    } catch (e) {
                        alert("Export failed: " + e.message);
                    } finally {
                        btn.disabled = false;
                        btn.innerText = originalText;
                    }
                });


                // Generate PDF Button Handler
                document.getElementById('mr-generate-btn').addEventListener('click', async () => {
                    const targetDate = document.getElementById('mr-target-date').value;
                    const author = document.getElementById('mr-author-name').value;
                    const statusText = document.getElementById('mr-status-text');
                    const generateBtn = document.getElementById('mr-generate-btn');
                    const downloadBtn = document.getElementById('mr-download-btn');

                    if(!targetDate) { alert('Please select a date.'); return; }

                    generateBtn.disabled = true;
                    generateBtn.style.opacity = '0.5';
                    downloadBtn.style.display = 'none';
                    statusText.innerText = 'Triggering PDF generation task...';
                    statusText.style.color = '#aaa';

                    try {
                        const res = await fetch('/api/morning-report/generate', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ target_date: targetDate, author: author })
                        });
                        const data = await res.json();

                        if(data.task_id) {
                            statusText.innerText = 'Generating PDF & AI Insights...';
                            mrPollingInterval = setInterval(() => checkGenStatus(data.task_id, targetDate), 3000);
                        } else {
                            throw new Error('No task ID returned.');
                        }
                    } catch (e) {
                        statusText.innerText = `Error: ${e.message}`;
                        statusText.style.color = 'red';
                        generateBtn.disabled = false;
                        generateBtn.style.opacity = '1';
                    }
                });

                async function checkGenStatus(taskId, targetDate) {
                    try {
                        const res = await fetch(`/api/morning-report/status/${taskId}`);
                        const data = await res.json();
                        const statusText = document.getElementById('mr-status-text');

                        if(data.state === 'SUCCESS' || data.status === 'SUCCESS') {
                            clearInterval(mrPollingInterval);
                            statusText.innerText = 'Report generated successfully!';
                            statusText.style.color = '#28a745';

                            const downloadBtn = document.getElementById('mr-download-btn');
                            downloadBtn.style.display = 'block';
                            downloadBtn.onclick = () => {
                                window.open(`/api/morning-report/download/${targetDate}`, '_blank');
                            };

                            document.getElementById('mr-generate-btn').disabled = false;
                            document.getElementById('mr-generate-btn').style.opacity = '1';

                            // Refresh Archive
                            loadMrArchive();
                        } else if(data.status === 'FAILED' || data.status === 'FAILURE') {
                            clearInterval(mrPollingInterval);
                            statusText.innerText = `Generation Failed: ${data.error || 'Unknown Error'}`;
                            statusText.style.color = 'red';
                            document.getElementById('mr-generate-btn').disabled = false;
                            document.getElementById('mr-generate-btn').style.opacity = '1';
                        }
                    } catch (e) {
                        console.error('Error polling Gen status', e);
                    }
                }
// script end
// script start
// script start
// script start
// script start
// script start
// script start
// script start
// script start
// script start
// script start
// script start

// script start
        // --- Main Tab Logic ---
        const MAIN_TABS_ORDER = ['terminal', 'ai_analyze', 'derivatives', 'history', 'import', 'corporate_actions', 'audit', 'config'];

        function switchMainTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.main-tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.main-tab').forEach(el => el.classList.remove('active'));

            // Show target
            const target = document.getElementById(`tab-${tabName}`);
            if (target) {
                target.classList.add('active');
            } else {
                console.warn(`Tab ${tabName} not found`);
                return;
            }

            const tabBtn = document.querySelector(`.main-tab[data-target="${tabName}"]`);
            if (tabBtn) tabBtn.classList.add('active');

            // Trigger specific refreshes if needed
            if (tabName === 'terminal' && window.ChartTabs) ChartTabs.resizeAll();
            if (tabName === 'import' && window.uploader) window.uploader.open();
            if (tabName === 'audit') loadAuditHistory(); // Auto-load audit on switch
            if (tabName === 'ai_analyze') fetchSystemAccuracy();
            if (tabName === 'derivatives') {
                // Initialize first sub-tab if none selected
                if (!document.querySelector('.deriv-sub-tab.active')) {
                    switchDerivTab('matrix');
                } else if (document.querySelector('#deriv-tab-market').classList.contains('active')) {
                    if (typeof loadMarketActivity === 'function') loadMarketActivity();
                } else if (document.querySelector('#deriv-tab-matrix').classList.contains('active') && document.getElementById('mr-data-body').innerHTML.includes('No data')) {
                     // Automatically load NIFTY snapshot if empty
                     if (typeof loadTimeseriesData === 'function') loadTimeseriesData(false);
                }
            }

            // Note: corporate_actions load is handled by the wrapper function below
        }

        // --- Derivatives Sub-Tab Logic ---
        function switchDerivTab(tabName) {
            document.querySelectorAll('.deriv-sub-tab').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.deriv-sub-tab').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('#tab-derivatives .wb-tab').forEach(el => {
                el.classList.remove('active');
                el.style.borderBottomColor = 'transparent';
                el.style.color = '#888';
            });

            const target = document.getElementById(`deriv-tab-${tabName}`);
            const btn = document.getElementById(`deriv-tab-btn-${tabName}`);
            if (target && btn) {
                if (target.id === 'deriv-tab-market') {
                    target.style.display = 'flex';
                } else if (target.id === 'deriv-tab-matrix') {
                    target.style.display = 'flex';
                } else if (target.id === 'deriv-tab-oi') {
                    target.style.display = 'flex';
                } else {
                    target.style.display = 'block';
                }
                target.classList.add('active');
                btn.classList.add('active');
                btn.style.borderBottomColor = '#4ade80';
                btn.style.color = '#fff';

                // Trigger chart loading if Market Activity
                if (tabName === 'market' && typeof loadMarketActivity === 'function') {
                    loadMarketActivity();
                }

                // Trigger options charts if OI Analysis
                if (tabName === 'oi' && typeof loadOptionsAnalysis === 'function') {
                    loadOptionsAnalysis();
                }

                // Trigger Volatility Analysis
                if (tabName === 'optanalysis' && typeof loadVolatilityAnalysis === 'function') {
                    loadVolatilityAnalysis();
                }
            }
        }

        // Initialize sub-tabs
        document.addEventListener('DOMContentLoaded', () => {
            switchDerivTab('matrix');
        });

        // --- Corporate Actions & Board Meetings UI ---
        let caCurrentTab = 'actions';
        let issueCurrentStatus = 'active';
        let caRawData = [];
        let caSortCol = 'date';
        let caSortAsc = false;


        function switchIssueStatus(status) {
            issueCurrentStatus = status;
            document.querySelectorAll('.status-tab').forEach(btn => {
                btn.style.color = '#a1a1aa';
                btn.style.borderBottomColor = 'transparent';
                if(btn.dataset.status === status) {
                    btn.style.color = '#4ade80';
                    btn.style.borderBottomColor = '#4ade80';
                }
            });
            renderCorporateActionsTable();
        }
        function filterCATable() { renderCorporateActionsTable(); }
        function switchCATab(tab) {
            caCurrentTab = tab;

            // UI Toggle
            document.getElementById('ca-tab-btn-actions').classList.toggle('active', tab === 'actions');
            document.getElementById('ca-tab-btn-announcements').classList.toggle('active', tab === 'announcements');
            document.getElementById('ca-tab-btn-meetings').classList.toggle('active', tab === 'meetings');
            document.getElementById('ca-tab-btn-rights').classList.toggle('active', tab === 'rights');
            document.getElementById('ca-tab-btn-ofs').classList.toggle('active', tab === 'ofs');
            document.getElementById('ca-tab-btn-tender').classList.toggle('active', tab === 'tender');
            document.getElementById('ca-tab-btn-circulars').classList.toggle('active', tab === 'circulars');

            // Show sub-tabs for Rights, OFS, Tender
            const issueTabs = ['rights', 'ofs', 'tender'];
            const tabsEl = document.getElementById('issue-status-tabs');
            if(issueTabs.includes(tab)) {
                if(tabsEl) tabsEl.style.display = 'flex';
                // Always reset to active on switch
                if(issueCurrentStatus !== 'active') switchIssueStatus('active');
            } else {
                if(tabsEl) tabsEl.style.display = 'none';
            }

            document.getElementById('ca-actions-filters').style.display = tab === 'actions' ? 'flex' : 'none';
            document.getElementById('ca-meetings-filters').style.display = tab === 'meetings' ? 'flex' : 'none';
            document.getElementById('ca-public-filters').style.display = tab === 'public' ? 'flex' : 'none';
            // Need a filter container for rights to prevent errors if we attempt to read it
            // but we don't have special filters for it, so nothing to show

            // Toggle table containers
            const isCirculars = tab === 'circulars';
            document.getElementById('ca-table-container').style.display = isCirculars ? 'none' : 'block';
            document.getElementById('ca-controls-wrapper').style.display = isCirculars ? 'none' : 'flex';
            document.querySelector('.history-status-bar').style.display = isCirculars ? 'none' : 'flex';
            document.getElementById('circulars-container').style.display = isCirculars ? 'block' : 'none';

            if (isCirculars) {
                loadCirculars();
                return;
            }

            // Clear current filters
            document.querySelectorAll('.ca-filter-cb').forEach(cb => cb.checked = false);
            document.getElementById('ca-search-input').value = '';

            // Reset state and load
            caRawData = [];
            if (tab === 'actions') caSortCol = 'exDate';
            else if (tab === 'announcements') caSortCol = 'dt'; // Announcement date
            else if (tab === 'meetings') caSortCol = 'date'; // Event cal date
            else caSortCol = 'recordDate'; // Public

            caSortAsc = false; // Descending by default

            loadCorporateActionsData();
        }

        async function loadCorporateActionsData() {
            const tbody = document.getElementById('ca-main-body');
            const thead = document.getElementById('ca-main-head');
            const statusMsg = document.getElementById('ca-status-msg');
            const rowCount = document.getElementById('ca-row-count');

            tbody.innerHTML = '<tr><td colspan="10" style="text-align:center; color:#888;">Loading data from NSE...</td></tr>';
            statusMsg.innerText = "Loading...";
            rowCount.innerText = "0 Rows";

            let endpoint = '/api/proxy/corporate-actions';
            if (caCurrentTab === 'announcements') endpoint = '/api/proxy/announcements';
            if (caCurrentTab === 'meetings') endpoint = '/api/proxy/event-calendar';
            if (caCurrentTab === 'rights') endpoint = '/api/proxy/rights';
            if (caCurrentTab === 'ofs') endpoint = '/api/proxy/ofs';
            if (caCurrentTab === 'tender') endpoint = '/api/proxy/tender';

            try {
                const response = await fetch(endpoint);
                if (!response.ok) throw new Error(`API Error: ${response.status}`);
                const data = await response.json();

                // Usually data is in an array or wrapped in a `data` key
                caRawData = Array.isArray(data) ? data : (data.data || []);

                // Format dates for sorting
                caRawData.forEach(item => {
                    if (item.exDate && item.exDate !== '-') item._date = new Date(item.exDate);
                    else if (item.bm_date && item.bm_date !== '-') item._date = new Date(item.bm_date);
                    else if (item.recordDate && item.recordDate !== '-') item._date = new Date(item.recordDate);
                    else item._date = new Date(0);

                    if (item.recDate && item.recDate !== '-') item._recDate = new Date(item.recDate);
                    else item._recDate = new Date(0);
                });

                renderCAHeaders();
                filterCATable();
            } catch (err) {
                tbody.innerHTML = `<tr><td colspan="10" style="text-align:center; color:#f44336;">Failed to load data: ${err.message}</td></tr>`;
                statusMsg.innerText = "Error";
                rowCount.innerText = "0 Rows";
            }
        }

        function renderCAHeaders() {
            const thead = document.getElementById('ca-main-head');
            thead.innerHTML = '';

            const tr = document.createElement('tr');
            let cols = [];
            if (caCurrentTab === 'actions') {
                cols = [
                    { id: 'symbol', label: 'Symbol' },
                    { id: 'comp', label: 'Company' },
                    { id: 'subject', label: 'Purpose' },
                    { id: 'faceVal', label: 'Face Value' },
                    { id: 'exDate', label: 'Ex-Date' },
                    { id: 'recDate', label: 'Record Date' },
                    { id: 'attachment', label: 'Attachment' }
                ];
            } else if (caCurrentTab === 'announcements') {
                cols = [
                    { id: 'symbol', label: 'Symbol' },
                    { id: 'sm_name', label: 'Company' },
                    { id: 'desc', label: 'Subject' },
                    { id: 'an_dt', label: 'Date' },
                    { id: 'attchmntFile', label: 'Attachment' }
                ];
            } else if (caCurrentTab === 'meetings') {
                cols = [
                    { id: 'symbol', label: 'Symbol' },
                    { id: 'company', label: 'Company' },
                    { id: 'purpose', label: 'Purpose' },
                    { id: 'bm_desc', label: 'Details' },
                    { id: 'date', label: 'Meeting Date' },
                    { id: 'attachment', label: 'Attachment' }
                ];
            } else if (caCurrentTab === 'rights' || caCurrentTab === 'ofs' || caCurrentTab === 'tender') {
                cols = [
                    { id: 'nseSymbol', label: 'Symbol' },
                    { id: 'companyName', label: 'Company' },
                    { id: 'issue_type', label: 'Type' },
                    { id: 'rightRatio', label: 'Details / Ratio' },
                    { id: 'stage', label: 'Stage' },
                    { id: 'offerPrice', label: 'Offer Price' },
                    { id: 'issueOpenDate', label: 'Open Date' },
                    { id: 'issueCloseDate', label: 'Close Date' },
                    { id: 'recordDate', label: 'Record Date' },
                    { id: 'attachment', label: 'Attachment' }
                ];
            }

            cols.forEach(c => {
                const th = document.createElement('th');
                let text = c.label;
                if (caSortCol === c.id) {
                    text += caSortAsc ? ' ▲' : ' ▼';
                    th.style.color = '#fff';
                }
                th.innerText = text;
                th.onclick = () => {
                    if (caSortCol === c.id) caSortAsc = !caSortAsc;
                    else { caSortCol = c.id; caSortAsc = true; }
                    filterCATable();
                };
                tr.appendChild(th);
            });
            thead.appendChild(tr);
        }

        // Helper function for Levenshtein distance based fuzzy matching in JS
        function levenshtein(a, b) {
            if (a.length === 0) return b.length;
            if (b.length === 0) return a.length;
            const matrix = [];
            for (let i = 0; i <= b.length; i++) matrix[i] = [i];
            for (let j = 0; j <= a.length; j++) matrix[0][j] = j;
            for (let i = 1; i <= b.length; i++) {
                for (let j = 1; j <= a.length; j++) {
                    if (b.charAt(i - 1) === a.charAt(j - 1)) {
                        matrix[i][j] = matrix[i - 1][j - 1];
                    } else {
                        matrix[i][j] = Math.min(matrix[i - 1][j - 1] + 1, Math.min(matrix[i][j - 1] + 1, matrix[i - 1][j] + 1));
                    }
                }
            }
            return matrix[b.length][a.length];
        }

        function isFuzzyMatch(query, target) {
            if (!query) return true;
            if (!target) return false;
            // Simple subset match
            if (target.includes(query)) return true;

            // Fuzzy distance match (allow 1 typo per 4 characters)
            const threshold = Math.max(1, Math.floor(query.length / 4));

            // Check substrings
            const words = target.split(/[\s_-]+/);
            for (let w of words) {
                if (Math.abs(w.length - query.length) <= threshold) {
                    if (levenshtein(query, w) <= threshold) return true;
                }
            }
            return false;
        }

        function filterCATable() {
            if (!caRawData || caRawData.length === 0) return;

            const search = document.getElementById('ca-search-input').value.toLowerCase().trim();

            let activeFilters = [];
            let filterContainerId = '';
            if (caCurrentTab === 'actions') filterContainerId = 'ca-actions-filters';
            else if (caCurrentTab === 'meetings') filterContainerId = 'ca-meetings-filters';
            else if (caCurrentTab === 'rights' || caCurrentTab === 'ofs' || caCurrentTab === 'tender') filterContainerId = 'ca-public-filters';

            if (filterContainerId) {
                activeFilters = Array.from(document.querySelectorAll(`#${filterContainerId} .ca-filter-cb:checked`)).map(cb => cb.value.toLowerCase());
            }


            let filtered = caRawData.filter(item => {
                // Search Match (Fuzzy)
                const sym = (item.symbol || item.bm_symbol || item.nseSymbol || '').toLowerCase();
                const comp = (item.comp || item.sm_name || item.companyName || item.company || '').toLowerCase();

                if (search && !isFuzzyMatch(search, sym) && !isFuzzyMatch(search, comp)) return false;

                // Status Filter for Rights, OFS, Tender
                if (caCurrentTab === 'rights' || caCurrentTab === 'ofs' || caCurrentTab === 'tender') {
                    const status = (item.status || item.stage || '').toLowerCase();
                    if (issueCurrentStatus && issueCurrentStatus !== 'all' && status !== issueCurrentStatus.toLowerCase()) {
                        return false;
                    }
                }


                // Advanced Filters
                if (activeFilters.length > 0) {
                    if (caCurrentTab === 'rights' || caCurrentTab === 'ofs' || caCurrentTab === 'tender') {
                        const issueType = (item.issue_type || '').toLowerCase();
                        let match = false;
                        for (const f of activeFilters) {
                            if (issueType === f) { match = true; break; }
                        }
                        if (!match) return false;
                    } else if (caCurrentTab === 'actions' || caCurrentTab === 'meetings') {
                        const purpose = (item.subject || item.bm_purpose || item.bm_desc || '').toLowerCase();
                        let match = false;
                        for (const f of activeFilters) {
                            if (purpose.includes(f)) { match = true; break; }
                            // Special handling for AGM/EGM
                            if (f === 'agm' && (purpose.includes('annual general meeting') || purpose.includes('extra ordinary general meeting'))) {
                                match = true; break;
                            }
                        }
                        if (!match) return false;
                    }
                }

                return true;
            });

            // Sort
            filtered.sort((a, b) => {
                let valA = a[caSortCol] || '';
                let valB = b[caSortCol] || '';

                // Use the parsed date object if sorting by a date column
                const parseDateStr = (dateStr) => {
                    if (!dateStr || dateStr === '-') return new Date(0);
                    const parts = dateStr.split('-');
                    if (parts.length === 3) {
                        const monthMap = { 'Jan':0, 'Feb':1, 'Mar':2, 'Apr':3, 'May':4, 'Jun':5, 'Jul':6, 'Aug':7, 'Sep':8, 'Oct':9, 'Nov':10, 'Dec':11 };
                        let mIndex = monthMap[parts[1].charAt(0).toUpperCase() + parts[1].slice(1).toLowerCase()];
                        if (mIndex !== undefined) return new Date(parts[2], mIndex, parseInt(parts[0], 10));
                    }
                    return new Date(0);
                };

                if (caSortCol === 'exDate' || caSortCol === 'bm_date' || caSortCol === 'recordDate' || caSortCol === 'issueOpenDate' || caSortCol === 'issueCloseDate' || caSortCol === 'dateOfBrdResIssueApproving') {
                    // Rights dates aren't fully pre-parsed in loadCorporateActionsData so parse on the fly or use existing _date
                    valA = a._date ? a._date.getTime() : parseDateStr(a[caSortCol]).getTime();
                    valB = b._date ? b._date.getTime() : parseDateStr(b[caSortCol]).getTime();
                } else if (caSortCol === 'recDate') {
                    valA = a._recDate ? a._recDate.getTime() : 0;
                    valB = b._recDate ? b._recDate.getTime() : 0;
                }

                if (valA < valB) return caSortAsc ? -1 : 1;
                if (valA > valB) return caSortAsc ? 1 : -1;
                return 0;
            });

            renderCATableData(filtered);
        }

        function renderCATableData(data) {
            const tbody = document.getElementById('ca-main-body');
            tbody.innerHTML = '';

            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="10" style="text-align:center; color:#888;">No data found matching criteria.</td></tr>';
                document.getElementById('ca-status-msg').innerText = "Ready";
                document.getElementById('ca-row-count').innerText = "0 Rows";
                return;
            }

            data.forEach(item => {
                const tr = document.createElement('tr');

                // Highlighting logic
                let rowColor = '';
                const purpose = (item.subject || item.bm_purpose || item.bm_desc || '').toLowerCase();
                if (purpose.includes('dividend')) rowColor = 'rgba(76, 175, 80, 0.15)'; // Soft green
                else if (purpose.includes('bonus') || purpose.includes('split')) rowColor = 'rgba(0, 188, 212, 0.15)'; // Soft cyan
                else if (purpose.includes('financial results')) rowColor = 'rgba(255, 152, 0, 0.15)'; // Soft orange

                if (rowColor) tr.style.backgroundColor = rowColor;

                const findLink = (obj) => {
                    let possibleKeys = ['attchmntFile', 'circFilelink', 'attachment', 'link', 'xmlFileName'];
                    for (let k of possibleKeys) {
                        if (obj[k]) return obj[k];
                    }
                    return null;
                };

                const linkVal = findLink(item);
                const linkUrl = linkVal ? (linkVal.startsWith('http') ? linkVal : `https://www.nseindia.com${linkVal}`) : '#';
                const linkHtml = linkVal ? `<a href="${linkUrl}" target="_blank" style="color: #4ade80; text-decoration: underline;">View PDF</a>` : '-';

                if (caCurrentTab === 'actions') {
                    tr.innerHTML = `
                        <td><strong>${item.symbol || '-'}</strong></td>
                        <td style="white-space:normal; max-width:200px;">${item.comp || '-'}</td>
                        <td style="white-space:normal; max-width:300px;">${item.subject || '-'}</td>
                        <td>${item.faceVal !== undefined && item.faceVal !== null ? item.faceVal : '-'}</td>
                        <td>${item.exDate || '-'}</td>
                        <td>${item.recDate || '-'}</td>
                        <td>${linkHtml}</td>
                    `;
                } else if (caCurrentTab === 'announcements') {
                    // Format announcement date
                    let formattedDate = '-';
                    if (item.an_dt) {
                        try {
                            // "an_dt" is often "2024-11-20 17:34:00"
                            const dateObj = new Date(item.an_dt.replace(' ', 'T'));
                            formattedDate = isNaN(dateObj.getTime()) ? item.an_dt.split(' ')[0] : dateObj.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
                        } catch(e) {
                            formattedDate = item.an_dt.split(' ')[0] || item.an_dt;
                        }
                    } else if (item.dt) {
                        formattedDate = item.dt;
                    }

                    tr.innerHTML = `
                        <td><strong>${item.symbol || '-'}</strong></td>
                        <td style="white-space:normal; max-width:200px;">${item.sm_name || '-'}</td>
                        <td style="white-space:normal; max-width:400px;">${item.desc || '-'}</td>
                        <td>${formattedDate}</td>
                        <td>${linkHtml}</td>
                    `;
                } else if (caCurrentTab === 'meetings') {
                     tr.innerHTML = `
                        <td><strong>${item.symbol || item.bm_symbol || '-'}</strong></td>
                        <td style="white-space:normal; max-width:200px;">${item.company || item.sm_name || '-'}</td>
                        <td style="white-space:normal; max-width:150px;">${item.purpose || item.bm_purpose || '-'}</td>
                        <td style="white-space:normal; max-width:300px;">${item.bm_desc || '-'}</td>
                        <td>${item.date || item.bm_date || '-'}</td>
                        <td>${linkHtml}</td>
                    `;
                } else if (caCurrentTab === 'rights' || caCurrentTab === 'ofs' || caCurrentTab === 'tender') {
                    // Rights, OFS, Tender
                    let typeBadge = '';
                    if (item.issue_type === 'ofs') typeBadge = '<span class="badge" style="background:#2196F3; padding:2px 6px; border-radius:3px; color:white; font-size:11px;">OFS</span>';
                    else if (item.issue_type === 'tender') typeBadge = '<span class="badge" style="background:#FF9800; padding:2px 6px; border-radius:3px; color:white; font-size:11px;">Tender</span>';
                    else if (item.issue_type === 'rights') typeBadge = '<span class="badge" style="background:#4CAF50; padding:2px 6px; border-radius:3px; color:white; font-size:11px;">Rights</span>';
                    else typeBadge = item.issue_type || '-';

                     tr.innerHTML = `
                        <td><strong>${item.nseSymbol || '-'}</strong></td>
                        <td style="white-space:normal; max-width:200px;">${item.companyName || '-'}</td>
                        <td>${typeBadge}</td>
                        <td style="white-space:normal; max-width:200px;">${item.rightRatio || item.purpose || item.details || '-'}</td>
                        <td>${item.stage || item.status || '-'}</td>
                        <td>${item.offerPrice || item.price || '-'}</td>
                        <td>${item.issueOpenDate || '-'}</td>
                        <td>${item.issueCloseDate || '-'}</td>
                        <td>${item.recordDate || '-'}</td>
                        <td>${linkHtml}</td>
                    `;
                }
                tbody.appendChild(tr);
            });

            // Re-render headers to update sort arrows
            renderCAHeaders();

            document.getElementById('ca-status-msg').innerText = "Loaded successfully";
            document.getElementById('ca-row-count').innerText = `${data.length} Rows`;
        }

        function exportCATableCSV() {
            const thead = document.getElementById('ca-main-head');
            const tbody = document.getElementById('ca-main-body');

            if (tbody.rows.length === 0 || tbody.innerText.includes('Loading') || tbody.innerText.includes('No data')) {
                alert("No data to export.");
                return;
            }

            let csv = [];
            const headers = Array.from(thead.querySelectorAll('th')).map(th => `"${th.innerText.replace(/[▲▼]/g, '').trim()}"`);
            csv.push(headers.join(","));

            Array.from(tbody.querySelectorAll('tr')).forEach(tr => {
                const row = Array.from(tr.querySelectorAll('td')).map(td => `"${td.innerText.replace(/"/g, '""')}"`);
                csv.push(row.join(","));
            });

            const blob = new Blob([csv.join("\n")], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.setAttribute('hidden', '');
            a.setAttribute('href', url);
            let filename = 'Corporate_Actions';
            if (caCurrentTab === 'meetings') filename = 'Board_Meetings';
            else if (caCurrentTab === 'announcements') filename = 'Announcements';
            else if (caCurrentTab === 'rights') filename = 'Rights_Issues';
            else if (caCurrentTab === 'rights' || caCurrentTab === 'ofs' || caCurrentTab === 'tender') filename = caCurrentTab.charAt(0).toUpperCase() + caCurrentTab.slice(1);

            a.setAttribute('download', `NSE_${filename}_${new Date().toISOString().slice(0,10)}.csv`);
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        }

        // Trigger load Corporate Actions when switchMainTab is called (override existing hook)
        const _originalSwitchMainTab = switchMainTab;
        switchMainTab = function(tabName) {
            _originalSwitchMainTab(tabName);
            if (tabName === 'corporate_actions' && caRawData.length === 0) {
                // Initial load
                switchCATab('actions');
            }
        };

        // --- Proxy Scrapers ---
        async function loadRights() {
            document.getElementById('rights-container').innerHTML = '<p>Loading Rights data from NSE...</p>';
            try {
                const response = await fetch('/api/proxy/rights');
                const data = await response.json();

                // NSE typically returns data inside an array or inside {data: []}
                const items = Array.isArray(data) ? data : (data.data || []);
                document.getElementById('rights-container').innerHTML = renderGenericProxyTable(items);
            } catch(e) {
                document.getElementById('rights-container').innerHTML = `<p style="color:red;">Error loading rights: ${e.message}</p>`;
            }
        }

        async function loadCirculars() {
            const container = document.getElementById('circulars-container');
            container.innerHTML = '<p>Loading Circulars data from DB/NSE...</p>';
            try {
                const response = await fetch('/api/proxy/circulars');
                const data = await response.json();
                const items = Array.isArray(data) ? data : (data.data || []);

                if (items.length === 0) {
                    container.innerHTML = "<p>No circulars found.</p>";
                    return;
                }

                let html = `
                <div class="table-wrapper" style="max-height: 600px; overflow-y: auto; border: 1px solid #333; border-radius: 4px;">
                    <table class="data-table" style="width: 100%;">
                        <thead style="position: sticky; top: 0; background: #222; z-index: 10;">
                            <tr>
                                <th style="padding: 8px;">Date</th>
                                <th style="padding: 8px;">Circular No.</th>
                                <th style="padding: 8px;">Department</th>
                                <th style="padding: 8px;">Subject</th>
                                <th style="padding: 8px;">Link</th>
                            </tr>
                        </thead>
                        <tbody>`;

                items.forEach(item => {
                    const linkUrl = item.circFile ? (item.circFile.startsWith('http') ? item.circFile : `https://www.nseindia.com${item.circFile}`) : '#';
                    const linkHtml = item.circFile ? `<a href="${linkUrl}" target="_blank" style="color: #4ade80; text-decoration: underline;">View PDF</a>` : '-';
                    html += `
                            <tr>
                                <td style="padding: 8px; white-space: nowrap;">${item.circDate || '-'}</td>
                                <td style="padding: 8px; white-space: nowrap;">${item.circNo || '-'}</td>
                                <td style="padding: 8px; white-space: nowrap;">${item.circDepartment || '-'}</td>
                                <td style="padding: 8px; min-width: 300px;">${item.sub || item.subject || '-'}</td>
                                <td style="padding: 8px;">${linkHtml}</td>
                            </tr>`;
                });

                html += `</tbody></table></div>`;
                container.innerHTML = html;
            } catch(e) {
                container.innerHTML = `<p style="color:red;">Error loading circulars: ${e.message}</p>`;
            }
        }

        function renderGenericProxyTable(dataList) {
            if(!dataList || dataList.length === 0) return "<p>No entries found (API returned empty data or was blocked by WAF).</p>";

            // Collect keys that look interesting (not deep objects)
            const keys = Object.keys(dataList[0]).filter(k =>
                typeof dataList[0][k] !== 'object' && !k.startsWith('_')
            ).slice(0, 10); // Limit to 10 cols for sanity

            let html = `<table class="history-table"><thead><tr>`;
            keys.forEach(k => html += `<th>${k.toUpperCase().replace(/_/g, ' ')}</th>`);
            html += `</tr></thead><tbody>`;

            dataList.forEach(item => {
                html += `<tr>`;
                keys.forEach(k => {
                    let val = item[k] || '';
                    if (typeof val === 'string' && (k.toLowerCase().includes('link') || k.toLowerCase() === 'url' || val.startsWith('http'))) {
                        let linkUrl = val;
                        if(val.startsWith('/') && !val.startsWith('//')) {
                            linkUrl = 'https://www.nseindia.com' + val; // Handle relative links from NSE
                        }
                        // For display, truncate long URLs
                        let displayVal = val.length > 50 ? val.substring(0, 47) + '...' : val;
                        html += `<td><a href="${linkUrl}" target="_blank" style="color:#00bcd4; text-decoration:underline;" title="${val}">${displayVal}</a></td>`;
                    } else {
                        if(typeof val === 'string' && val.length > 100) val = val.substring(0, 97) + '...';
                        html += `<td title="${item[k]}">${val}</td>`;
                    }
                });
                html += `</tr>`;
            });
            html += `</tbody></table>`;
            return html;
        }


        // --- AI-Analyze Logic ---
        let aiWs = null;

        async function fetchSystemAccuracy() {
            try {
                const res = await fetch('/api/ai/accuracy?session_id=local_trader_01');
                if(res.ok) {
                    const data = await res.json();
                    document.getElementById('accuracy-score').innerText = `${data.accuracy}%`;
                }
            } catch(e) {
                console.warn("Could not fetch AI accuracy", e);
            }
        }

        function handleAiCmd(e) {
            const inputEl = document.getElementById('ai-cmd-input');

            // Auto-resize logic
            setTimeout(() => {
                inputEl.style.height = 'auto';
                inputEl.style.height = (inputEl.scrollHeight) + 'px';
            }, 0);

            if (e.key === 'Escape') {
                if (aiWs && aiWs.readyState === WebSocket.OPEN) {
                    aiWs.send(JSON.stringify({command: "STOP"}));
                    aiWs.close();
                    document.getElementById('ai-chat-feed').innerHTML += `
                    <div class="chat-message error-message" style="padding: 10px 0; border-bottom: 1px solid #222;">
                        <div style="color: #b8860b; font-weight: bold; margin-bottom: 5px;">[SYSTEM]</div>
                        <div class="log-line text-warning">[INTERRUPT] Execution halted by user.</div>
                    </div>`;
                }
            } else if (e.key === 'Enter') {
                if (e.shiftKey) {
                    // Allow multi-line
                    return;
                }
                e.preventDefault(); // Prevent default enter behavior (newline)
                const cmd = inputEl.value.trim();
                if (cmd.toUpperCase() === 'STOP') {
                    if (aiWs && aiWs.readyState === WebSocket.OPEN) {
                        aiWs.send(JSON.stringify({command: "STOP"}));
                        aiWs.close();
                        document.getElementById('ai-chat-feed').innerHTML += `
                        <div class="chat-message error-message" style="padding: 10px 0; border-bottom: 1px solid #222;">
                            <div style="color: #b8860b; font-weight: bold; margin-bottom: 5px;">[SYSTEM]</div>
                            <div class="log-line text-warning">[INTERRUPT] Execution halted by STOP command.</div>
                        </div>`;
                    }
                    inputEl.value = '';
                    inputEl.style.height = 'auto'; // Reset size
                    return;
                }
                runAiAnalysis(cmd);
                inputEl.style.height = 'auto'; // Reset size
            }
        }

        function runAiAnalysis(cmd) {
            if (!cmd) return;

            const groqKey = sessionStorage.getItem('GROQ_API_KEY');
            const openrouterKey = sessionStorage.getItem('OPENROUTER_API_KEY');
            const googleKey = sessionStorage.getItem('GOOGLE_API_KEY');

            const feedContainer = document.getElementById('ai-analysis-feed');
            const chatFeed = document.getElementById('ai-chat-feed');
            const cmdInput = document.getElementById('ai-cmd-input');

            // Show Feed
            feedContainer.style.display = 'flex';

            // Clear default team members and append initial user command
            chatFeed.innerHTML = `
                <div class="chat-message user-message" style="padding: 10px 0; border-bottom: 1px solid #222;">
                    <div style="color: #ccc; font-weight: bold; margin-bottom: 5px;">[TRADER]</div>
                    <div class="log-line">> EXEC: ${cmd}</div>
                </div>
            `;

            if (!groqKey || !openrouterKey || !googleKey) {
                chatFeed.innerHTML += `
                <div class="chat-message error-message" style="padding: 10px 0; border-bottom: 1px solid #222;">
                    <div style="color: #b8860b; font-weight: bold; margin-bottom: 5px;">[SYSTEM ERROR]</div>
                    <div class="log-line text-warning">[ERROR] Missing API keys. Please set them in Config tab.</div>
                </div>`;
                cmdInput.value = '';
                return;
            }

            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            aiWs = new WebSocket(`${protocol}//${window.location.host}/ws/ai-analyze`);

            aiWs.onopen = () => {
                aiWs.send(JSON.stringify({
                    command: cmd,
                    keys: { groq: groqKey, openrouter: openrouterKey, google: googleKey },
                    session_id: "local_trader_01"
                }));
                cmdInput.value = '';
                cmdInput.placeholder = "Processing... (Press ESC to stop)";
                cmdInput.readOnly = true;
            };

            let currentQuantLogicBlock = null;

            aiWs.onmessage = (event) => {
                const msg = JSON.parse(event.data);

                if (msg.type === "status") {
                    chatFeed.innerHTML += `
                        <div class="chat-message status-message" style="padding: 10px 0; border-bottom: 1px solid #222;">
                            <div class="log-line text-emerald" style="font-size: 0.9em;">[SYSTEM] ${msg.message}</div>
                        </div>`;
                } else if (msg.type === "jules_task") {
                    let julesOutput = `
                    <div class="chat-message jules-message" style="padding: 10px 0; border-bottom: 1px solid #222;">
                        <div style="color: #00bcd4; font-weight: bold; margin-bottom: 5px;">[JULES PRE-PROCESS]</div>`;

                    if (msg.reasoning) {
                        julesOutput += `
                        <details style="margin-bottom: 10px;">
                            <summary style="cursor: pointer; color: #a0a0a0; font-size: 0.9em;">[Thought Process]</summary>
                            <div style="padding: 10px; border-left: 2px solid #334155; margin-top: 5px; color: #888; background: #1a1c23;">
                                ${msg.reasoning.replace(/\n/g, '<br>')}
                            </div>
                        </details>`;
                    }
                    julesOutput += `<div class="log-line" style="color: #e0e0e0;"><strong>Final Task:</strong><br>${msg.message.replace(/\n/g, '<br>')}</div></div>`;
                    chatFeed.innerHTML += julesOutput;
                } else if (msg.type === "engine_type") {
                    chatFeed.innerHTML += `
                        <div class="chat-message status-message" style="padding: 10px 0; border-bottom: 1px solid #222;">
                            <div class="log-line text-muted" style="font-size: 0.9em;">>> Dispatched to Engine: ${msg.data.toUpperCase()}</div>
                        </div>`;
                } else if (msg.type === "quant_logic") {
                    if (!currentQuantLogicBlock) {
                        // Create new block for quant logic
                        const id = "quant-logic-" + Date.now();
                        chatFeed.insertAdjacentHTML('beforeend', `
                        <div class="chat-message deepseek-message" id="${id}" style="padding: 10px 0; border-bottom: 1px solid #222;">
                            <details>
                                <summary style="cursor: pointer; color: #64748b; font-weight: bold; margin-bottom: 5px;">[DEEPSEEK-R1] QUANT LOGIC</summary>
                                <div class="quant-content" style="color: #aaa; line-height: 1.5; white-space: pre-wrap; padding-left: 20px;"></div>
                            </details>
                        </div>`);
                        currentQuantLogicBlock = document.getElementById(id).querySelector('.quant-content');
                        currentQuantLogicBlock._inThink = false;
                    }

                    let token = msg.token;

                    if (token.includes("<think>")) {
                        token = token.replace("<think>", "");
                        currentQuantLogicBlock._inThink = true;

                        const detailsHtml = `<details open style="margin-bottom: 10px; margin-top: 10px;">
                            <summary style="cursor: pointer; color: #a0a0a0; font-size: 0.9em;">[Thought Process]</summary>
                            <div class="think-tag" style="padding: 10px; border-left: 2px solid #334155; margin-top: 5px; color: #888; background: #1a1c23; font-style: normal; display: block;"></div>
                        </details>`;
                        currentQuantLogicBlock.insertAdjacentHTML('beforeend', detailsHtml);
                    }

                    let isClosing = false;
                    if (token.includes("</think>")) {
                        token = token.replace("</think>", "");
                        isClosing = true;
                    }

                    if (token) {
                        if (currentQuantLogicBlock._inThink) {
                            const thinkTags = currentQuantLogicBlock.querySelectorAll('.think-tag');
                            if (thinkTags.length > 0) {
                                // Safe escape for innerHTML append inside think tag
                                let safeToken = token.replace(/</g, "&lt;").replace(/>/g, "&gt;");
                                thinkTags[thinkTags.length - 1].innerHTML += safeToken;
                            } else {
                                // Fallback
                                currentQuantLogicBlock.insertAdjacentText('beforeend', token);
                            }
                        } else {
                            // If we use innerHTML += here, we wipe out the <details> state (like if it was closed)
                            // Better to use insertAdjacentText to just append text node safely
                            currentQuantLogicBlock.insertAdjacentText('beforeend', token);
                        }
                    }

                    if (isClosing) {
                        currentQuantLogicBlock._inThink = false;
                    }
                } else if (msg.type === "data_matrix") {
                    const d = msg.data;
                    let matrixOutput = `
                    <div class="chat-message qwen-message" style="padding: 10px 0; border-bottom: 1px solid #222;">
                        <div style="color: #e6a23c; font-weight: bold; margin-bottom: 5px;">[QWEN] DATA MATRIX</div>`;

                    if (d.qwen_reasoning) {
                        matrixOutput += `
                        <details style="margin-bottom: 10px;">
                            <summary style="cursor: pointer; color: #a0a0a0; font-size: 0.9em;">[Thought Process]</summary>
                            <div style="padding: 10px; border-left: 2px solid #334155; margin-top: 5px; color: #888; background: #1a1c23;">
                                ${d.qwen_reasoning.replace(/\n/g, '<br>')}
                            </div>
                        </details>`;
                    }

                    matrixOutput += `
                        <table class="ai-dense-table" style="width: 100%; border-collapse: collapse; font-size: 0.9em; border: 1px solid #333; margin-top: 10px;">
                            <thead>
                                <tr>
                                    <th style="border: 1px solid #333; padding: 8px; background: #16181d; color: #888; text-align: left;">SYMBOL</th>
                                    <th style="border: 1px solid #333; padding: 8px; background: #16181d; color: #888; text-align: left;">OPEN_INT</th>
                                    <th style="border: 1px solid #333; padding: 8px; background: #16181d; color: #888; text-align: left;">CHG_OI</th>
                                    <th style="border: 1px solid #333; padding: 8px; background: #16181d; color: #888; text-align: left;">IV</th>
                                    <th style="border: 1px solid #333; padding: 8px; background: #16181d; color: #888; text-align: left;">IMPLIED_MOVE</th>
                                </tr>
                            </thead>
                            <tbody>`;

                    let hasData = false;
                    if(d.equity && d.equity.close_price) {
                        hasData = true;
                        const fallbackLabel = d.yfinance_fallback ? ' <span style="color:#cca700; font-size: 0.8em;">(YF)</span>' : '';
                        matrixOutput += `
                            <tr>
                                <td style="border: 1px solid #333; padding: 8px;">${d.ticker} (EQ)${fallbackLabel}</td>
                                <td style="border: 1px solid #333; padding: 8px;">${(d.equity.total_traded_qty || 0).toLocaleString()} Vol</td>
                                <td style="border: 1px solid #333; padding: 8px;">-</td>
                                <td style="border: 1px solid #333; padding: 8px;">-</td>
                                <td style="border: 1px solid #333; padding: 8px;">₹${d.equity.close_price}</td>
                            </tr>
                        `;
                    }
                    if(d.futures && d.futures.close_price) {
                        hasData = true;
                        let oiColor = (d.futures.change_in_oi > 0) ? 'color: #10b981;' : 'color: #f59e0b;';
                        let oiSign = (d.futures.change_in_oi > 0) ? '+' : '';
                        matrixOutput += `
                            <tr>
                                <td style="border: 1px solid #333; padding: 8px;">${d.ticker}-FUT</td>
                                <td style="border: 1px solid #333; padding: 8px;">${(d.futures.open_interest || 0).toLocaleString()}</td>
                                <td style="border: 1px solid #333; padding: 8px; ${oiColor}">${oiSign}${(d.futures.change_in_oi || 0).toLocaleString()}</td>
                                <td style="border: 1px solid #333; padding: 8px;">-</td>
                                <td style="border: 1px solid #333; padding: 8px;">± ${d.futures.implied_move_pct || 0}%</td>
                            </tr>
                        `;
                    }
                    if(!hasData) {
                        matrixOutput += `<tr><td colspan="5" style="border: 1px solid #333; padding: 8px; text-align: center;">No specific DB or YFinance rows found for ${d.ticker}.</td></tr>`;
                    }
                    matrixOutput += `</tbody></table>`;

                    if (d.local_db_history || d.yfinance_history) {
                        matrixOutput += `<div style="margin-top: 10px; font-size: 0.85em; color: #a0a0a0;">`;
                        if (d.local_db_history && d.local_db_history.ticker) {
                            matrixOutput += `<details style="margin-bottom: 5px;">
                                <summary style="cursor: pointer; color: #4ade80;">[View Local DB Context: Volatility, P/E, Corp Actions]</summary>
                                <pre style="background: #111; padding: 10px; border-radius: 4px; overflow-x: auto; margin-top: 5px; color: #888;">${JSON.stringify(d.local_db_history, null, 2)}</pre>
                            </details>`;
                        }
                        if (d.yfinance_history && d.yfinance_history.history) {
                            matrixOutput += `<details style="margin-bottom: 5px;">
                                <summary style="cursor: pointer; color: #60a5fa;">[View YFinance Context: Recent History & News]</summary>
                                <pre style="background: #111; padding: 10px; border-radius: 4px; overflow-x: auto; margin-top: 5px; color: #888;">${JSON.stringify(d.yfinance_history, null, 2)}</pre>
                            </details>`;
                        }
                        matrixOutput += `</div>`;
                    }

                    matrixOutput += `</div>`;
                    chatFeed.innerHTML += matrixOutput;

                } else if (msg.type === "governance_log") {
                    chatFeed.innerHTML += `
                    <div class="chat-message llama-message" style="padding: 10px 0; border-bottom: 1px solid #222;">
                        <details>
                            <summary style="cursor: pointer; color: #b8860b; font-weight: bold; margin-bottom: 5px;">[GPT 120B] COMPLIANCE JUDGE</summary>
                            <div class="log-line text-warning" style="padding-left: 20px;">> ${msg.message}</div>
                        </details>
                    </div>`;
                } else if (msg.type === "execution") {
                    const ex = msg.data;
                    let actionColor = ex.action.toUpperCase().includes('SHORT') || ex.action.toUpperCase().includes('SELL') ? 'color: #f59e0b;' : 'color: #10b981;';
                    let rationaleHtml = "";
                    if (Array.isArray(ex.rationale)) {
                        rationaleHtml = "<ul style='margin-top: 5px; margin-bottom: 0; padding-left: 20px; color: #ccc;'>" + ex.rationale.map(r => `<li>${r}</li>`).join('') + "</ul>";
                    } else {
                        rationaleHtml = ex.rationale;
                    }

                    let execOutput = `
                    <div class="chat-message gemini-message" style="padding: 10px 0; border-bottom: 1px solid #222;">
                        <div style="color: #00bcd4; font-weight: bold; margin-bottom: 5px;">[GEMINI] EXECUTION</div>`;

                    if (ex.reasoning) {
                        execOutput += `
                        <details style="margin-bottom: 15px;">
                            <summary style="cursor: pointer; color: #a0a0a0; font-size: 0.9em;">[Thought Process]</summary>
                            <div style="padding: 10px; border-left: 2px solid #334155; margin-top: 5px; color: #888; background: #1a1c23;">
                                ${ex.reasoning.replace(/\n/g, '<br>')}
                            </div>
                        </details>`;
                    }

                    execOutput += `
                        <div class="exec-confidence" title="Calculated based on data completeness and alignment with reasoning." style="font-size: 0.85em; color: #888; margin-bottom: 5px;">CONF_SCORE: ${ex.confidence}% <span style="font-size: 0.8em; cursor: help;">(?)</span></div>
                        <div class="exec-directive" style="font-size: 1.3em; font-weight: bold; margin-bottom: 10px; ${actionColor}">ACTION: ${ex.action.toUpperCase()}</div>
                        <div class="exec-details" style="font-size: 0.9em; color: #ccc; line-height: 1.6; border-top: 1px dotted #333; padding-top: 10px;">
                            TARGET: ₹${ex.target} | STOP_LOSS: ₹${ex.stop_loss}<br><br>
                            <strong>RATIONALE:</strong><br> ${rationaleHtml}
                        </div>
                    </div>`;
                    chatFeed.innerHTML += execOutput;
                } else if (msg.type === "error") {
                    chatFeed.innerHTML += `
                    <div class="chat-message error-message" style="padding: 10px 0; border-bottom: 1px solid #222;">
                        <div style="color: #b8860b; font-weight: bold; margin-bottom: 5px;">[SYSTEM ERROR]</div>
                        <div class="log-line text-warning">[ERROR] ${msg.message}</div>
                    </div>`;
                } else if (msg.type === "done") {
                    cmdInput.placeholder = "_";
                    cmdInput.readOnly = false;
                    cmdInput.focus();
                    aiWs.close();
                    currentQuantLogicBlock = null;
                }

                // Auto-scroll chat feed
                chatFeed.scrollTop = chatFeed.scrollHeight;
            };

            aiWs.onerror = () => {
                chatFeed.innerHTML += `
                <div class="chat-message error-message" style="padding: 10px 0; border-bottom: 1px solid #222;">
                    <div style="color: #b8860b; font-weight: bold; margin-bottom: 5px;">[SYSTEM ERROR]</div>
                    <div class="log-line text-warning">[ERROR] WebSocket connection failed. Is backend running?</div>
                </div>`;
                cmdInput.placeholder = "_";
                cmdInput.readOnly = false;
            };

            aiWs.onclose = () => {
                 cmdInput.placeholder = "_";
                 cmdInput.readOnly = false;
                 currentQuantLogicBlock = null;
            }
        }

        // Global Shortcut Handler
        document.addEventListener('keydown', (e) => {
            // Avoid shortcuts when typing in inputs (except special keys if needed)
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

            // Alt+Key for Tab Switching
            if (e.altKey && !e.ctrlKey && !e.shiftKey) {
                const key = e.key.toLowerCase();
                const map = {
                    't': 'terminal',
                    'h': 'history',
                    'i': 'import',
                    'a': 'ai_analyze',
                    'u': 'audit',
                    'c': 'config'
                };
                if (map[key]) {
                    e.preventDefault();
                    switchMainTab(map[key]);
                }
            }

            // Ctrl+PageUp/Down for Cycling Tabs (Excel-like)
            if (e.ctrlKey && (e.key === 'PageUp' || e.key === 'PageDown')) {
                e.preventDefault();
                const currentTab = document.querySelector('.main-tab.active');
                if (currentTab) {
                    const currentId = currentTab.dataset.target;
                    let idx = MAIN_TABS_ORDER.indexOf(currentId);
                    if (idx !== -1) {
                        if (e.key === 'PageDown') {
                            idx = (idx + 1) % MAIN_TABS_ORDER.length;
                        } else {
                            idx = (idx - 1 + MAIN_TABS_ORDER.length) % MAIN_TABS_ORDER.length;
                        }
                        switchMainTab(MAIN_TABS_ORDER[idx]);
                    }
                }
            }
        });

        // --- History Logic (Ported from data_viewer.html) ---
        let currentHistoryData = [];
        let currentSortColumn = null;
        let currentSortOrder = 'asc'; // 'asc' or 'desc'

        function updateHistoryControls() {
            const type = document.getElementById('data-type').value;
            const symbolGroup = document.getElementById('symbol-group');
            const instrumentGroup = document.getElementById('instrument-group');

            if (['fao_participant_oi', 'fii_stats', 'india_vix'].includes(type)) {
                symbolGroup.style.display = 'none';
                document.getElementById('symbol-input').value = '';
            } else {
                symbolGroup.style.display = 'flex';
            }

            if (type === 'bhavcopy_fo') {
                instrumentGroup.style.display = 'flex';
            } else {
                instrumentGroup.style.display = 'none';
                document.getElementById('instrument-input').value = 'ALL';
            }

            // Clear table on type change
            clearHistoryTable();
            // Reset sorting
            currentSortColumn = null;
            currentSortOrder = 'asc';
        }

        function clearHistoryTable() {
            document.getElementById('history-body').innerHTML = '';
            document.getElementById('history-head').innerHTML = '';
            document.getElementById('history-status-msg').innerText = "Ready";
            document.getElementById('history-row-count').innerText = "0 Rows";
            currentHistoryData = [];
        }

        async function loadHistoryData(sortBy = null, sortOrder = 'asc') {
            const type = document.getElementById('data-type').value;
            const symbol = document.getElementById('symbol-input').value.trim();
            const start = document.getElementById('start-date').value;
            const end = document.getElementById('end-date').value;
            const instrument = document.getElementById('instrument-input') ? document.getElementById('instrument-input').value : 'ALL';

            // Use current sort state if not explicitly passed
            if (!sortBy && currentSortColumn) {
                sortBy = currentSortColumn;
                sortOrder = currentSortOrder;
            }

            // Clear previous data immediately
            clearHistoryTable();
            document.getElementById('history-status-msg').innerText = "Loading...";

            const tbody = document.getElementById('history-body');
            tbody.innerHTML = '<tr><td colspan="100" style="text-align:center; color:#888;">Loading data...</td></tr>';

            const btn = document.querySelector('button[onclick="loadHistoryData()"]');
            if(btn) { btn.disabled = true; btn.innerText = "Loading..."; }

            try {
                let url = `/api/data/view/list?type=${type}&limit=500`; // Removed timestamp for speed, browser cache is usually fine with varying params
                if (symbol) url += `&symbol=${symbol}`;
                if (start) url += `&start_date=${start}`;
                if (end) url += `&end_date=${end}`;
                if (type === 'bhavcopy_fo' && instrument !== 'ALL') url += `&instrument=${instrument}`;

                // Add Server-Side Sorting Params
                if (sortBy) {
                    url += `&sort_by=${sortBy}&sort_order=${sortOrder}`;
                    currentSortColumn = sortBy;
                    currentSortOrder = sortOrder;
                }

                const res = await fetch(url);
                if (!res.ok) throw new Error(await res.text());
                const data = await res.json();
                currentHistoryData = data; // Store

                if (data.length > 0 && Object.keys(data[0]).length === 0) {
                    throw new Error("Received rows but with no columns. Data structure error.");
                }

                renderHistoryTable(data);
                document.getElementById('history-status-msg').innerText = `Loaded ${data.length} rows`;
                document.getElementById('history-row-count').innerText = `${data.length} Rows`;

            } catch (e) {
                console.error("Load History Error:", e);
                document.getElementById('history-status-msg').innerText = "Error: " + e.message;
                const tbody = document.getElementById('history-body');
                tbody.innerHTML = `<tr><td colspan="100" style="text-align:center; color:red;">Error loading data: ${e.message}</td></tr>`;
            } finally {
                if(btn) { btn.disabled = false; btn.innerText = "Load Data"; }
            }
        }

        function renderHistoryTable(data) {
            const tbody = document.getElementById('history-body');
            const thead = document.getElementById('history-head');
            tbody.innerHTML = '';
            thead.innerHTML = '';

            if (!data || data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="100" style="text-align:center; color:#888;">No Data Found</td></tr>';
                return;
            }

            // Headers
            const keys = Object.keys(data[0]);
            const trHead = document.createElement('tr');
            keys.forEach((key, index) => {
                const th = document.createElement('th');

                // Sort Indicator
                let label = key.replace(/_/g, ' ').toUpperCase();
                if (key === currentSortColumn) {
                    label += (currentSortOrder === 'asc' ? ' ▲' : ' ▼');
                    th.style.color = '#fff'; // Highlight active sort column
                }

                th.innerText = label;
                th.onclick = () => sortHistoryTable(key); // Trigger Server-Side Sort
                trHead.appendChild(th);
            });
            thead.appendChild(trHead);

            // Rows
            data.forEach(row => {
                const tr = document.createElement('tr');
                keys.forEach(key => {
                    const td = document.createElement('td');
                    let val = row[key];
                    if (val === null || val === undefined) val = '-';
                    if (typeof val === 'number') {
                         // Smart formatting
                         if (Number.isInteger(val)) {
                             td.innerText = val.toLocaleString();
                         } else {
                             // Check for volatility columns or small numbers
                             if (key.includes('volatility') || key.includes('_vol') || key.includes('iv') || key.includes('rate')) {
                                 td.innerText = val.toFixed(4);
                             } else {
                                 td.innerText = val.toFixed(2);
                             }
                         }
                         td.style.textAlign = 'right';
                    } else {
                        td.innerText = val;
                    }
                    tr.appendChild(td);
                });
                tbody.appendChild(tr);
            });
        }

        function sortHistoryTable(key) {
            // Toggle order if clicking same column, else default to asc
            let order = 'asc';
            if (key === currentSortColumn) {
                order = (currentSortOrder === 'asc') ? 'desc' : 'asc';
            }

            // Reload data with new sort params
            loadHistoryData(key, order);
        }

        async function exportHistoryData() {
            const btn = document.querySelector('button[onclick="exportHistoryData()"]');
            const originalText = btn.innerText;
            btn.disabled = true;
            btn.innerHTML = '⏳ Exporting...'; // Simple spinner effect

            const type = document.getElementById('data-type').value;
            const symbol = document.getElementById('symbol-input').value.trim();
            const start = document.getElementById('start-date').value;
            const end = document.getElementById('end-date').value;
            const instrument = document.getElementById('instrument-input') ? document.getElementById('instrument-input').value : 'ALL';

            let url = `/api/data/view/export?type=${type}`;
            if (symbol) url += `&symbol=${symbol}`;
            if (start) url += `&start_date=${start}`;
            if (end) url += `&end_date=${end}`;
            if (type === 'bhavcopy_fo' && instrument !== 'ALL') url += `&instrument=${instrument}`;

            try {
                const response = await fetch(url);
                if (!response.ok) throw new Error(await response.text());

                // Create Blob and Download
                const blob = await response.blob();
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = downloadUrl;
                // Try to get filename from header or fallback
                const contentDisposition = response.headers.get('Content-Disposition');
                let filename = `${type}_export.csv`;
                if (contentDisposition) {
                    const match = contentDisposition.match(/filename=(.+)/);
                    if (match && match.length > 1) filename = match[1];
                }
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(downloadUrl);
            } catch (e) {
                console.error("Export Failed:", e);
                alert("Export failed: " + e.message);
            } finally {
                btn.disabled = false;
                btn.innerText = originalText;
            }
        }

        // --- Audit Logic ---
        function toggleDateInputs(checkbox) {
            const startInput = document.getElementById('start-date');
            const endInput = document.getElementById('end-date');
            if (checkbox.checked) {
                startInput.value = '';
                endInput.value = '';
                startInput.disabled = true;
                endInput.disabled = true;
            } else {
                startInput.disabled = false;
                endInput.disabled = false;
            }
        }

        async function deleteHistoryData() {
            const dt = document.getElementById('data-type').value;
            const sym = document.getElementById('symbol-input').value.trim();
            let start = document.getElementById('start-date').value;
            let end = document.getElementById('end-date').value;
            const isAllDates = document.getElementById('all-dates-check').checked;

            if (isAllDates) {
                start = '1900-01-01';
                end = '2100-12-31';
            }

            if (!start || !end) {
                alert("Please select both 'From' and 'To' dates to delete data within a range (or check 'All Dates').");
                return;
            }

            const msg = isAllDates ?
                `Are you sure you want to DELETE ALL DATA for '${dt}' across all dates? This will also delete the import logs so you can re-import later. THIS CANNOT BE UNDONE.` :
                `Are you sure you want to DELETE all data for '${dt}' from ${start} to ${end}? This will also delete the import logs so you can re-import later. THIS CANNOT BE UNDONE.`;

            if (!confirm(msg)) {
                return;
            }

            const btn = document.querySelector('.btn-danger');
            if(btn) { btn.disabled = true; btn.innerText = "Deleting..."; }

            try {
                const params = new URLSearchParams({
                    type: dt,
                    start_date: start,
                    end_date: end
                });

                const res = await fetch(`/api/data/view/range?${params.toString()}`, {
                    method: 'DELETE'
                });

                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail || "Deletion failed");
                }
                const data = await res.json();
                alert(`Successfully deleted ${data.records_deleted} records and ${data.logs_deleted} import logs.`);
                loadHistoryData(); // Reload to show empty
            } catch (e) {
                alert(`Error: ${e.message}`);
            } finally {
                if(btn) { btn.disabled = false; btn.innerText = "Delete Data"; }
            }
        }

        async function loadAuditHistory() {
            const start = document.getElementById('audit-start').value;
            const end = document.getElementById('audit-end').value;
            const level = document.getElementById('audit-level') ? document.getElementById('audit-level').value : 'ALL';
            const tbody = document.getElementById('audit-log-body');
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;">Loading...</td></tr>';

             try {
                let url = '/api/audit/history?limit=1000';
                if (start) url += `&start_date=${start}`;
                if (end) url += `&end_date=${end}`;
                if (level && level !== 'ALL') url += `&level=${level}`;
                const res = await fetch(url);
                const logs = await res.json();
                tbody.innerHTML = '';

                if(logs.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:#888;">No logs found for period</td></tr>';
                    return;
                }

                // Render logs in reverse chronological order (latest top if API sends latest first, usually)
                // Assuming API sends latest first. If not, reverse.
                // Log object: {timestamp, source, level, message}
                logs.forEach(log => {
                     const tr = document.createElement('tr');

                     // Style based on level
                     let color = '#d4d4d4';
                     if (log.level === 'ERROR') color = '#f48771';
                     else if (log.level === 'WARNING') color = '#cca700';

                     tr.style.color = color;

                     tr.innerHTML = `
                        <td>${log.timestamp.replace('T', ' ')}</td>
                        <td>${log.source}</td>
                        <td>${log.level}</td>
                        <td>${log.message}</td>
                     `;
                     tbody.appendChild(tr);
                });
                document.getElementById('log-count').innerText = `${logs.length} Events`;
             } catch(e) {
                 tbody.innerHTML = `<tr><td colspan="4" style="color:red;">Error loading logs: ${e.message}</td></tr>`;
             }
        }

        function downloadLogs() {
             const rows = Array.from(document.querySelectorAll('#audit-log-body tr'));
             if(rows.length === 0 || rows[0].innerText.includes('Loading')) return;

             let csv = "Timestamp,Source,Level,Message\n";
             rows.forEach(row => {
                 const cols = Array.from(row.querySelectorAll('td'));
                 if(cols.length < 4) return; // Skip message rows
                 const line = cols.map(c => `"${c.innerText.replace(/"/g, '""')}"`).join(",");
                 csv += line + "\n";
             });

             const blob = new Blob([csv], {type: "text/csv"});
             const link = document.createElement("a");
             link.href = URL.createObjectURL(blob);
             link.download = `Audit_Trail_${new Date().toISOString().slice(0,10)}.csv`;
             link.click();
        }

        // --- Init ---
        window.onload = () => {
            Layout.init();
            ChartTabs.init();
            WorkbookManager.init();
            connectLiveFeed();

            // Setup clock
            const dtEl = document.getElementById('global-datetime');
            setInterval(() => {
                if (dtEl) {
                    const now = new Date();
                    dtEl.innerText = now.toLocaleString();
                }
            }, 1000);

            // Set default dates
            const today = new Date().toISOString().split('T')[0];
            if(document.getElementById('end-date')) document.getElementById('end-date').value = today;
            if(document.getElementById('audit-end')) document.getElementById('audit-end').value = today;

            // Override Layout shortcuts or Uploader open
            if(window.uploader) {
                // We keep uploader logic for progress polling, but override open
                window.uploader.open = () => switchMainTab('import');
            }

            // Initialize Chat Input Handler
            const chatInput = document.getElementById('jules-input');
            const chatContent = document.getElementById('jules-content');
            if(chatInput) {
                chatInput.addEventListener('keypress', async (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        const msg = chatInput.value.trim();
                        if (!msg) return;
                        chatContent.innerHTML += `<div class="msg user" style="color:#00bcd4; margin-top:5px;"><strong>You:</strong> ${msg}</div>`;
                        chatInput.value = '';
                        // Mock Response for now as actual backend call wasn't fully visible in my read but I recall the structure
                        try {
                            const res = await fetch('/api/jules/chat', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({message: msg})
                            });
                            const data = await res.json();
                            chatContent.innerHTML += `<div class="msg jules" style="margin-top:5px;"><strong>Jules:</strong> ${data.response}</div>`;
                        } catch(err) {
                            chatContent.innerHTML += `<div class="msg error" style="color:red;">Error: ${err.message}</div>`;
                        }
                    }
                });
            }
        };

        function switchLeftTab(tab) {
             document.getElementById('jules-content').style.display = tab === 'jules' ? 'block' : 'none';
             document.getElementById('python-content').style.display = tab === 'python' ? 'block' : 'none';
             document.querySelectorAll('#lp-bottom .tab-btn').forEach(b => b.classList.remove('active'));
             if(tab === 'jules') document.querySelector('#lp-bottom .tab-btn:first-child').classList.add('active');
             else document.querySelector('#lp-bottom .tab-btn:last-child').classList.add('active');
        }

        let ws, logsWs;
        function connectLiveFeed() {
             const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
             ws = new WebSocket(`${protocol}//${window.location.host}/ws/live`);
             ws.onopen = () => { console.log("WS Connected"); ws.send(JSON.stringify({subscribe: ["NIFTY", "BANKNIFTY"]})); };
             ws.onmessage = (event) => {
                 const data = JSON.parse(event.data);
                 if(window.ChartTabs) ChartTabs.handleTick(data);
                 if(window.WorkbookManager) WorkbookManager.handleTick(data);
             };

             logsWs = new WebSocket(`${protocol}//${window.location.host}/ws/logs`);
             logsWs.onmessage = (event) => {
                 const msg = event.data;
                 const auditContainer = document.getElementById('audit-log-container');
                 if(auditContainer) {
                     const div = document.createElement('div');
                     div.innerText = msg;
                     div.style.borderBottom = '1px solid #333';
                     // Color coding
                     if (msg.includes("ERROR")) div.style.color = "#f48771";
                     else if (msg.includes("WARNING")) div.style.color = "#cca700";
                     else div.style.color = "#d4d4d4";

                     auditContainer.appendChild(div);
                     if(auditContainer.scrollHeight - auditContainer.scrollTop < 200) auditContainer.scrollTop = auditContainer.scrollHeight;
                 }

                 // Uvicorn logs via WebSocket
                 const terminal = document.getElementById('uvicorn-terminal');
                 if (terminal && !msg.includes("MainProcess") && !msg.includes("celery") && !msg.includes("NSE_Importer")) {
                     const div = document.createElement('div');
                     div.innerText = msg;
                     if (msg.includes("ERROR")) div.style.color = "#f48771";
                     else if (msg.includes("WARNING")) div.style.color = "#cca700";
                     else div.style.color = "#d4d4d4";
                     terminal.appendChild(div);
                     // Auto-scroll
                     if(terminal.scrollHeight - terminal.scrollTop < 300) terminal.scrollTop = terminal.scrollHeight;
                 }
             };

             // Polling for Celery logs from DB since they don't share the same WS loop
             let lastCeleryLogId = 0;
             setInterval(async () => {
                 const celeryTerminal = document.getElementById('celery-terminal');
                 if(!celeryTerminal || celeryTerminal.offsetParent === null) return; // Only poll if visible

                 // ONLY poll if an import is actually running, to prevent infinite looping and DB spam
                 if (!window.uploader || !window.uploader.isPolling) {
                     return;
                 }

                 try {
                     // We fetch the latest audit logs that are likely from celery
                     const res = await fetch(`/api/audit/history?limit=50`);
                     if(res.ok) {
                         const logs = await res.json();
                         // Sort ascending by ID or timestamp
                         logs.sort((a,b) => a.id - b.id);

                         // On first load, don't dump 200 logs, just get the last 20
                         if (lastCeleryLogId === 0 && logs.length > 0) {
                             lastCeleryLogId = logs[Math.max(0, logs.length - 20)].id - 1;
                         }

                         let newLogs = logs.filter(l => l.id > lastCeleryLogId && l.source === 'NSE_Importer');
                         if(newLogs.length > 0) {
                             lastCeleryLogId = newLogs[newLogs.length - 1].id;
                             newLogs.forEach(log => {
                                 const div = document.createElement('div');
                                 div.innerText = `[${log.timestamp.replace('T', ' ').substring(0, 19)}] ${log.level} [${log.source}] ${log.message}`;
                                 if (log.level === "ERROR" || log.level === "FAILED") div.style.color = "#f48771";
                                 else if (log.level === "WARNING") div.style.color = "#cca700";
                                 else div.style.color = "#d4d4d4";
                                 celeryTerminal.appendChild(div);
                             });
                             celeryTerminal.scrollTop = celeryTerminal.scrollHeight;
                         }
                     }
                 } catch(e) {
                     // silent fail for poller
                 }
             }, 2000);
        }
// script end
// script start
// script start
    let echartInstance = null;
    let fiiDiiChartInstance = null;
    let participantChartInstance = null;

    async function loadMarketActivity() {
        const symbol = document.getElementById('market-activity-symbol').value.toUpperCase() || 'NIFTY';

        // 1. Load FII/DII Chart (Side by side bars per user request)
        try {
            const res = await fetch('/api/market-activity/cash-flow');
            const data = await res.json();
            if (fiiDiiChartInstance) fiiDiiChartInstance.destroy();
            const ctx = document.getElementById('fiiDiiChart').getContext('2d');

            // Extract Nifty prices dynamically if returned
            const niftyData = data.nifty_close || [];

            // Add NIFTY line overlay dynamically to FII/DII Chart if NIFTY exists
            const datasets = [
                { label: 'FII Net', type: 'bar', yAxisID: 'y', data: data.fii_net, backgroundColor: '#E88B1E', borderColor: '#E88B1E', borderWidth: 1 }, // Orange
                { label: 'DII Net', type: 'bar', yAxisID: 'y', data: data.dii_net, backgroundColor: '#3176B8', borderColor: '#3176B8', borderWidth: 1 }  // Blue
            ];

            if (niftyData.length > 0) {
                datasets.push({
                    label: 'NIFTY',
                    type: 'line',
                    yAxisID: 'y1',
                    data: niftyData,
                    borderColor: '#ff9900',
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.1
                });
            }

            let minNifty = null;
            let maxNifty = null;
            if (niftyData.length > 0) {
                const validNifty = niftyData.filter(v => v !== null && !isNaN(v));
                if (validNifty.length > 0) {
                    const absMin = Math.min(...validNifty);
                    const absMax = Math.max(...validNifty);
                    const diff = absMax - absMin;
                    const pad = diff * 0.1;
                    minNifty = Math.floor(absMin - pad);
                    maxNifty = Math.ceil(absMax + pad);
                }
            }

            fiiDiiChartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.dates,
                    datasets: datasets
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    scales: {
                        x: { stacked: false },
                        y: { stacked: false, position: 'left', grid: { color: '#333' } },
                        y1: {
                            type: 'linear', position: 'right', display: niftyData.length > 0, grid: { drawOnChartArea: false },
                            min: minNifty, max: maxNifty
                        }
                    },
                    plugins: { legend: { labels: { color: '#ccc' } } }
                }
            });
        } catch (e) { console.error("Error loading FII/DII", e); }

        // 2. Load Participant OI Chart (Merged Daily Grouped Bar Chart)
        try {
            const days = document.getElementById('market-activity-days').value || '30';
            const res = await fetch(`/api/market-activity/participant-oi?days=${days}`);
            const data = await res.json();

            // Build grouped ECharts for daily snapshot
            const container = document.getElementById('participant-oi-daily-summary');
            if (participantChartInstance) participantChartInstance.dispose();
            participantChartInstance = echarts.init(container);

            const dates = data.dates || [];
            if (dates.length === 0) {
                container.innerHTML = '<p style="text-align:center; color:#888;">No Participant OI data found.</p>';
                return;
            }

            // Define 6 metric categories per user request
            const metrics = [
                { key: 'fut_idx', label: 'Index Futures' },
                { key: 'fut_stk', label: 'Stock Futures' },
                { key: 'opt_idx_ce', label: 'Index Calls' },
                { key: 'opt_idx_pe', label: 'Index Puts' },
                { key: 'opt_stk_ce', label: 'Stock Calls' },
                { key: 'opt_stk_pe', label: 'Stock Puts' }
            ];

            const participants = [
                { key: 'fii', label: 'FII', color: '#E88B1E' },     // Orange
                { key: 'dii', label: 'DII', color: '#3176B8' },     // Blue
                { key: 'pro', label: 'PRO', color: '#9B59B6' },     // Orange
                { key: 'client', label: 'CLI', color: '#00FF00' }  // Green
            ];

            const xAxisData = metrics.map(m => m.label);

            // We only care about the latest date (Today)
            const todayIdx = dates.length - 1;

            const series = participants.map(p => {
                const pData = metrics.map(m => {
                    const arrayKey = `${p.key}_${m.key}`;
                    const arr = data[arrayKey] || [];
                    return arr.length > todayIdx ? arr[todayIdx] : 0;
                });

                return {
                    name: p.label,
                    type: 'bar',
                    data: pData,
                    itemStyle: { color: p.color }
                };
            });

            const option = {
                backgroundColor: 'transparent',
                tooltip: {
                    trigger: 'axis',
                    axisPointer: { type: 'shadow' }
                },
                legend: {
                    data: participants.map(p => p.label),
                    textStyle: { color: '#ccc' }
                },
                grid: { left: '3%', right: '4%', bottom: '10%', top: '15%', containLabel: true },
                xAxis: {
                    type: 'category',
                    data: xAxisData,
                    axisLabel: { color: '#ccc', fontWeight: 'bold' },
                    axisLine: { lineStyle: { color: '#333' } },
                    axisTick: { alignWithLabel: true }
                },
                yAxis: {
                    type: 'value',
                    axisLabel: { color: '#888' },
                    splitLine: { lineStyle: { color: '#333', type: 'dashed' } }
                },
                series: series
            };

            participantChartInstance.setOption(option);

            // Trigger historical charts rendering next
            if (typeof renderParticipantHistorical === 'function') {
                renderParticipantHistorical(data);
            }

        } catch (e) { console.error("Error loading Participant OI", e); }

        // 3. Load EChart Multi-Axis
        const container = document.getElementById('echart-container');
        if (!echartInstance) {
            echartInstance = echarts.init(container, 'dark', { renderer: 'canvas' });
        }

        echartInstance.showLoading({ text: 'Loading Data...', color: '#4ade80', textColor: '#fff', maskColor: 'rgba(30, 30, 30, 0.8)' });

        try {
            const res = await fetch(`/api/market-activity/dynamic-chart/${symbol}`);
            if (!res.ok) throw new Error("Data fetch failed");
            const data = await res.json();

            const option = {
                backgroundColor: 'transparent',
                tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
                legend: { data: ['K-Line', 'MA20', 'Donchian Upper', 'Donchian Lower', 'Volume', 'ATR (14)', 'Future OI'] },
                grid: [
                    { left: '5%', right: '5%', height: '50%', top: '5%' }, // Main Chart
                    { left: '5%', right: '5%', top: '60%', height: '15%' }, // Volume
                    { left: '5%', right: '5%', top: '80%', height: '15%' }  // ATR / OI
                ],
                xAxis: [
                    { type: 'category', data: data.dates, gridIndex: 0, show: false },
                    { type: 'category', data: data.dates, gridIndex: 1, show: false },
                    { type: 'category', data: data.dates, gridIndex: 2 }
                ],
                yAxis: [
                    { scale: true, gridIndex: 0, splitLine: { show: true, lineStyle: { color: '#333' } } },
                    { scale: true, gridIndex: 1, splitNumber: 2, axisLabel: { formatter: (v) => (v/1000000).toFixed(1) + 'M' } },
                    { scale: true, gridIndex: 2, name: 'ATR %', splitNumber: 2, position: 'left' },
                    { scale: true, gridIndex: 2, name: 'Total OI', splitNumber: 2, position: 'right', axisLabel: { formatter: (v) => (v/1000000).toFixed(1) + 'M' } }
                ],
                dataZoom: [{ type: 'inside', xAxisIndex: [0, 1, 2], start: 50, end: 100 }, { show: true, type: 'slider', xAxisIndex: [0, 1, 2], bottom: '0%' }],
                series: [
                    { name: 'K-Line', type: 'candlestick', data: data.ohlc, itemStyle: { color: '#ef5350', color0: '#26a69a', borderColor: '#ef5350', borderColor0: '#26a69a' } },
                    { name: 'MA20', type: 'line', data: data.ma20, smooth: true, showSymbol: false, lineStyle: { width: 1, color: '#fff' } },
                    { name: 'Donchian Upper', type: 'line', data: data.donchian_upper, step: 'end', showSymbol: false, lineStyle: { type: 'dashed', color: '#ffeb3b', width: 1 } },
                    { name: 'Donchian Lower', type: 'line', data: data.donchian_lower, step: 'end', showSymbol: false, lineStyle: { type: 'dashed', color: '#ffeb3b', width: 1 } },
                    { name: 'Volume', type: 'bar', xAxisIndex: 1, yAxisIndex: 1, data: data.volume, itemStyle: { color: '#5470c6' } },
                    { name: 'ATR (14)', type: 'line', xAxisIndex: 2, yAxisIndex: 2, data: data.atr, showSymbol: false, lineStyle: { color: '#fac858' } },
                    { name: 'Future OI', type: 'line', xAxisIndex: 2, yAxisIndex: 3, data: data.oi, showSymbol: false, lineStyle: { color: '#ee6666' } }
                ]
            };

            echartInstance.setOption(option, true);
        } catch (e) {
            container.innerHTML = `<div style="color:red; text-align:center; padding-top: 200px;">Error: ${e.message}</div>`;
        } finally {
            echartInstance?.hideLoading();
        }
    }

    // Listen for resize
    window.addEventListener('resize', () => { if (echartInstance) echartInstance.resize(); });
// script end

let pcrChartInstance = null;
let highOiChartInstance = null;

async function loadOptionsAnalysis() {
    const symbol = document.getElementById('opt-analysis-symbol').value.toUpperCase();
    if (!symbol) return;

    // 1. Load 500-Day PCR Chart
    try {
        const res = await fetch(`/api/data/derivatives/pcr_history?symbol=${symbol}&days=500`);
        const data = await res.json();

        const chartDom = document.getElementById('opt-analysis-pcr-chart');
        if (pcrChartInstance) pcrChartInstance.dispose();
        pcrChartInstance = echarts.init(chartDom);

        const option = {
            backgroundColor: 'transparent',
            tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
            legend: { data: ['Total OI', 'Price (FUT1)', 'PCR'], textStyle: { color: '#ccc' } },
            grid: { left: '3%', right: '3%', bottom: '3%', top: '15%', containLabel: true },
            xAxis: {
                type: 'category',
                data: data.dates,
                axisLabel: { color: '#888' },
                axisLine: { lineStyle: { color: '#333' } }
            },
            yAxis: [
                {
                    type: 'value',
                    name: 'Total OI',
                    position: 'left',
                    splitLine: { show: false },
                    axisLabel: { color: '#888' },
                    nameTextStyle: { color: '#888' }
                },
                {
                    type: 'value',
                    name: 'Price (FUT1)',
                    position: 'right',
                    splitLine: { lineStyle: { color: '#333', type: 'dashed' } },
                    axisLabel: { color: '#888' },
                    nameTextStyle: { color: '#888' },
                    scale: true,
                    min: 'dataMin',
                    max: 'dataMax'
                },
                {
                    type: 'value',
                    name: 'PCR',
                    position: 'right',
                    offset: 60,
                    scale: true,
                    min: 'dataMin',
                    max: 'dataMax',
                    splitLine: { show: false },
                    axisLabel: { color: '#888' },
                    nameTextStyle: { color: '#888' }
                }
            ],
            dataZoom: [
                { type: 'inside', start: 50, end: 100 },
                { type: 'slider', start: 50, end: 100, textStyle: { color: '#ccc' } }
            ],
            series: [
                {
                    name: 'Total OI',
                    type: 'bar',
                    data: data.total_oi,
                    itemStyle: { color: 'rgba(54, 162, 235, 0.4)' },
                    yAxisIndex: 0
                },
                {
                    name: 'Price (FUT1)',
                    type: 'line',
                    data: data.price,
                    itemStyle: { color: '#FFCC00' }, // Classic yellow
                    lineStyle: { width: 2 },
                    symbol: 'none',
                    yAxisIndex: 1
                },
                {
                    name: 'PCR',
                    type: 'line',
                    data: data.pcr,
                    itemStyle: { color: '#00FF00' }, // Bright green
                    lineStyle: { width: 2 },
                    symbol: 'none',
                    yAxisIndex: 2
                }
            ]
        };
        pcrChartInstance.setOption(option);
    } catch (e) {
        console.error("Error loading PCR history:", e);
    }

    // Trigger load High OI Chart (Next step)
    if (typeof loadHighOI === 'function') {
        loadHighOI(symbol);
    }
}

async function loadHighOI(symbol) {
    try {
        const res = await fetch(`/api/data/derivatives/option_chain?symbol=${symbol}`);
        const data = await res.json();

        if (!data || !data.data || data.data.length === 0) {
            document.getElementById('opt-analysis-high-oi-chart').innerHTML = '<p style="text-align:center; color:#888;">No Option Chain data found.</p>';
            return;
        }

        const strikes = [];
        const ce_oi = [];
        const pe_oi = [];

        // Only take ATM +/- 20 strikes to avoid squished charts
        const sortedData = data.data.sort((a,b) => a.strike - b.strike);
        let atmIndex = 0;
        let minDiff = Infinity;

        for (let i = 0; i < sortedData.length; i++) {
            const diff = Math.abs(sortedData[i].strike - data.spot_price);
            if (diff < minDiff) {
                minDiff = diff;
                atmIndex = i;
            }
        }

        const startIdx = Math.max(0, atmIndex - 20);
        const endIdx = Math.min(sortedData.length, atmIndex + 20);
        const filteredData = sortedData.slice(startIdx, endIdx);

        filteredData.forEach(row => {
            strikes.push(row.strike);
            ce_oi.push(row.CE.oi || 0);
            pe_oi.push(row.PE.oi || 0);
        });

        const chartDom = document.getElementById('opt-analysis-high-oi-chart');
        if (highOiChartInstance) highOiChartInstance.dispose();
        highOiChartInstance = echarts.init(chartDom);

        const option = {
            backgroundColor: 'transparent',
            tooltip: {
                trigger: 'axis',
                axisPointer: { type: 'shadow' },
                formatter: function (params) {
                    let res = `<div style="font-weight:bold;">Strike: ${params[0].axisValue}</div>`;
                    params.forEach(function (p) {
                        const val = Math.abs(p.value).toLocaleString();
                        res += `<div style="color:${p.color};">${p.seriesName}: ${val}</div>`;
                    });
                    return res;
                }
            },
            legend: {
                data: ['Call OI', 'Put OI'],
                textStyle: { color: '#ccc' }
            },
            grid: { left: '3%', right: '4%', bottom: '10%', top: '10%', containLabel: true },
            xAxis: {
                type: 'category',
                data: strikes,
                axisLabel: { color: '#FFCC00', fontWeight: 'bold', rotate: 45 },
                axisLine: { show: true, lineStyle: { color: '#333' } },
                axisTick: { show: false },
                splitLine: { show: true, lineStyle: { color: '#222' } }
            },
            yAxis: {
                type: 'value',
                axisLabel: {
                    color: '#888',
                    formatter: function (value) { return Math.abs(value); }
                },
                splitLine: { lineStyle: { color: '#333', type: 'dashed' } }
            },
            series: [
                {
                    name: 'Call OI',
                    type: 'bar',
                    stack: 'Total',
                    label: { show: false },
                    itemStyle: { color: '#FF0000' }, // Classic Red for calls/resistance
                    data: ce_oi.map(v => -v) // Negative value to make it bar leftwards
                },
                {
                    name: 'Put OI',
                    type: 'bar',
                    stack: 'Total',
                    label: { show: false },
                    itemStyle: { color: '#00FF00' }, // Classic Green for puts/support
                    data: pe_oi
                }
            ]
        };

        // Format tooltip to show absolute values for Call OI
        option.tooltip.formatter = function (params) {
            let res = `<div style="font-weight:bold;">Strike: ${params[0].axisValue}</div>`;
            params.forEach(function (p) {
                const val = Math.abs(p.value).toLocaleString();
                res += `<div style="color:${p.color};">${p.seriesName}: ${val}</div>`;
            });
            return res;
        };

        // Format xAxis to show absolute values
        option.xAxis.axisLabel.formatter = function (value) {
            return Math.abs(value);
        };

        highOiChartInstance.setOption(option);
    } catch (e) {
        console.error("Error loading high OI chart:", e);
    }
}

let historicalChartInstances = {};

function renderParticipantHistorical(data) {
    const dates = data.dates || [];
    if (dates.length === 0) return;

    // We have 6 metrics = 6 charts
    const metrics = [
        { key: 'fut_idx', id: 'lsRatioEchart-idx-fut', label: 'Index Futures' },
        { key: 'fut_stk', id: 'lsRatioEchart-stk-fut', label: 'Stock Futures' },
        { key: 'opt_idx_ce', id: 'lsRatioEchart-idx-call', label: 'Index Calls' },
        { key: 'opt_idx_pe', id: 'lsRatioEchart-idx-put', label: 'Index Puts' },
        { key: 'opt_stk_ce', id: 'lsRatioEchart-stk-call', label: 'Stock Calls' },
        { key: 'opt_stk_pe', id: 'lsRatioEchart-stk-put', label: 'Stock Puts' }
    ];

    const participants = [
        { key: 'fii', label: 'FII', color: '#E88B1E' },
        { key: 'dii', label: 'DII', color: '#3176B8' },
        { key: 'pro', label: 'PRO', color: '#9B59B6' },
        { key: 'client', label: 'CLI', color: '#00FF00' }
    ];

    metrics.forEach(m => {
        const dom = document.getElementById(m.id);
        if (!dom) return;

        if (historicalChartInstances[m.key]) historicalChartInstances[m.key].dispose();
        const chart = echarts.init(dom);
        historicalChartInstances[m.key] = chart;

        // Extract series per participant for this specific metric
        const series = participants.map(p => {
            const arr = data[`${p.key}_${m.key}`] || [];
            return {
                name: p.label,
                type: 'bar',
                data: arr,
                itemStyle: { color: p.color }
            };
        });

        const option = {
            backgroundColor: 'transparent',
            tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
            legend: { data: participants.map(p => p.label), textStyle: { color: '#ccc' } },
            grid: { left: '3%', right: '4%', bottom: '15%', top: '15%', containLabel: true },
            xAxis: {
                type: 'category',
                data: dates,
                axisLabel: { color: '#888' },
                axisLine: { lineStyle: { color: '#333' } }
            },
            yAxis: [
                {
                    type: 'value',
                    name: 'Ratio',
                    axisLabel: { color: '#888' },
                    splitLine: { lineStyle: { color: '#333', type: 'dashed' } },
                    nameTextStyle: { color: '#888' }
                },
                {
                    type: 'value',
                    name: 'NIFTY',
                    position: 'right',
                    axisLabel: { color: '#ccc' },
                    splitLine: { show: false },
                    nameTextStyle: { color: '#ccc' },
                    scale: true
                }
            ],
            dataZoom: [
                { type: 'inside', start: 50, end: 100 },
                { type: 'slider', start: 50, end: 100, textStyle: { color: '#ccc' } }
            ],
            series: series.map(s => {
                return {
                    ...s,
                    // Center the datum at 1 for the L/S Ratio so ratios < 1 point downward
                    markLine: {
                        data: [{ yAxis: 1 }],
                        lineStyle: { color: '#444', type: 'solid', width: 2 },
                        symbol: 'none',
                        label: { show: false }
                    }
                };
            })
        };

        // ECharts has a specific property to set the datum line for bars
        option.series.forEach(s => { s.large = true; s.yAxisIndex = 0; });

        // Remove the manual min calculation which causes issues for negative numbers
        // option.yAxis[0].min = (value) => value.min < 0.5 ? 0 : value.min; // Give bottom room

        // Change datum to 1 instead of 0 for bars (since it's a ratio)
        option.series.forEach(s => { s.stack = null; });

        // Actually, the previous data arrays might be coming in as just net positions or large absolute numbers, not ratios centered around 1.
        // Wait, `data[..._fut_idx]` here comes from `/api/market-activity/participant-oi` which returns Net Positions (Long - Short), not ratios.
        // The net positions can be positive or negative natively.
        // We do NOT need to subtract 1 from these values.

        // Remove the data mapping since this is a Net Position chart, not an L/S Ratio chart.
        const transformedSeries = series.map(s => {
            return {
                ...s,
                data: s.data
            };
        });

        option.series = transformedSeries;

        // Let ECharts naturally scale Y-axis for Net Positions (which can be positive/negative)
        option.yAxis[0].min = null;

        // Add NIFTY overlay
        const niftyData = data.nifty_prices || data.nifty_close || [];
        if (niftyData.length > 0) {
            option.legend.data.push('NIFTY');
            option.series.push({
                name: 'NIFTY',
                type: 'line',
                data: niftyData,
                yAxisIndex: 1,
                itemStyle: { color: '#FFCC00' }, // Classic yellow line
                lineStyle: { width: 2 },
                symbol: 'none'
            });
        }

        // Relabel Y-axis to format absolute values for Net Position
        option.yAxis[0].axisLabel.formatter = function (value) {
            if (Math.abs(value) >= 1000) {
                return (value / 1000).toFixed(1) + 'k';
            }
            return value;
        };
        option.yAxis[0].name = "Net Pos (Qty)";

        // Fix the NIFTY line scaling so it isn't flat by forcing axis scale properties explicitly
        if (niftyData.length > 0) {
            const validNifty = niftyData.filter(v => v !== null && !isNaN(v));
            if (validNifty.length > 0) {
                const minNifty = Math.min(...validNifty);
                const maxNifty = Math.max(...validNifty);
                const diff = maxNifty - minNifty;
                const pad = diff * 0.1;
                option.yAxis[1].min = Math.floor(minNifty - pad);
                option.yAxis[1].max = Math.ceil(maxNifty + pad);
                option.yAxis[1].scale = false; // We use strict min/max now
            }
        } else {
            option.yAxis[1].scale = true;
        }

        // Remove the markline at 1 since Net Pos fluctuates around 0 naturally
        option.series.forEach(s => {
            if(s.markLine) {
                delete s.markLine;
            }
        });

        option.tooltip.formatter = function (params) {
            let res = `<div style="font-weight:bold;">${params[0].axisValue}</div>`;
            params.forEach(function (p) {
                if (p.seriesName === 'NIFTY') {
                    res += `<div style="color:${p.color};">${p.seriesName}: ${p.value.toLocaleString()}</div>`;
                } else {
                    res += `<div style="color:${p.color};">${p.seriesName}: ${p.value.toLocaleString()}</div>`;
                }
            });
            return res;
        };

        chart.setOption(option);
    });
}

let volPreExpiryChart = null;
let volConeChart = null;

async function loadVolatilityAnalysis() {
    const symbol = document.getElementById('vol-analysis-symbol').value.toUpperCase() || 'NIFTY';
    const expiryType = document.getElementById('vol-analysis-expiry-type').value;
    const lookback = document.getElementById('vol-analysis-lookback').value;
    const boxDays = document.getElementById('vol-analysis-box-days').value;

    // 1. Load Pre-Expiry Chart
    try {
        const preExpiryChartDom = document.getElementById('vol-pre-expiry-chart');
        if (volPreExpiryChart) volPreExpiryChart.dispose();
        volPreExpiryChart = echarts.init(preExpiryChartDom, 'dark', { renderer: 'canvas' });
        volPreExpiryChart.showLoading({ text: 'Loading...', color: '#4ade80', maskColor: 'rgba(30, 30, 30, 0.8)' });

        const res = await fetch(`/api/data/derivatives/pre_expiry_action/${symbol}?lookback_days=${lookback}&box_days=${boxDays}&expiry_type=${expiryType}`);
        const data = await res.json();

        if (data.detail) {
            console.error("API Error Pre-Expiry:", data.detail);
            volPreExpiryChart.hideLoading();
            alert("Error loading Pre-Expiry Action: " + data.detail);
            return;
        }

        const markLines = (data.expiries || []).map(exp => {
            return { xAxis: exp, label: { formatter: 'Exp', position: 'start' } };
        });

        const markAreas = (data.boxes || []).map(box => {
            return [
                { xAxis: box.start_date, itemStyle: { color: 'rgba(255, 204, 0, 0.2)' } },
                { xAxis: box.end_date }
            ];
        });

        const preExpiryOption = {
            backgroundColor: 'transparent',
            tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
            legend: { data: ['Price', `Realized Vol (${boxDays}D)`], textStyle: { color: '#ccc' } },
            grid: { left: '3%', right: '3%', bottom: '10%', top: '15%', containLabel: true },
            xAxis: {
                type: 'category',
                data: data.dates,
                axisLabel: { color: '#888' },
                axisLine: { lineStyle: { color: '#333' } }
            },
            yAxis: [
                {
                    type: 'value',
                    name: 'Price',
                    position: 'left',
                    scale: true,
                    splitLine: { lineStyle: { color: '#333' } },
                    axisLabel: { color: '#ccc' },
                    nameTextStyle: { color: '#ccc' }
                },
                {
                    type: 'value',
                    name: `RV (${boxDays}D) %`,
                    position: 'right',
                    scale: true,
                    splitLine: { show: false },
                    axisLabel: { color: '#888' },
                    nameTextStyle: { color: '#888' }
                }
            ],
            dataZoom: [{ type: 'inside' }, { type: 'slider', textStyle: { color: '#ccc' } }],
            series: [
                {
                    name: 'Price',
                    type: 'line',
                    data: data.prices,
                    yAxisIndex: 0,
                    itemStyle: { color: '#3176B8' }, // Blue line for price
                    lineStyle: { width: 2 },
                    showSymbol: false,
                    markLine: {
                        symbol: ['none', 'none'],
                        lineStyle: { color: '#ff4444', type: 'solid', width: 1 },
                        data: markLines
                    },
                    markArea: {
                        data: markAreas
                    }
                },
                {
                    name: `Realized Vol (${boxDays}D)`,
                    type: 'line',
                    data: data.rv,
                    yAxisIndex: 1,
                    itemStyle: { color: '#E88B1E' }, // Orange line for RV
                    lineStyle: { width: 2 },
                    showSymbol: false
                }
            ]
        };

        volPreExpiryChart.setOption(preExpiryOption);
        volPreExpiryChart.hideLoading();
    } catch (e) {
        console.error("Error loading Pre-Expiry Action", e);
        if (volPreExpiryChart) volPreExpiryChart.hideLoading();
    }

    // 2. Load Volatility Cone Chart
    try {
        const coneChartDom = document.getElementById('vol-cone-chart');
        if (volConeChart) volConeChart.dispose();
        volConeChart = echarts.init(coneChartDom, 'dark', { renderer: 'canvas' });
        volConeChart.showLoading({ text: 'Loading...', color: '#4ade80', maskColor: 'rgba(30, 30, 30, 0.8)' });

        const res = await fetch(`/api/data/derivatives/volatility_cone/${symbol}`);
        const data = await res.json();

        if (data.detail) {
            console.error("API Error Vol Cone:", data.detail);
            volConeChart.hideLoading();
            alert("Error loading Volatility Cone: " + data.detail);
            return;
        }

        const coneOption = {
            backgroundColor: 'transparent',
            title: { text: 'Realized Volatility Cone', textStyle: { color: '#ccc', fontSize: 14 } },
            tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
            legend: { data: ['Max', '75th Pct', 'Median', '25th Pct', 'Min', 'Current RV'], textStyle: { color: '#ccc' } },
            grid: { left: '3%', right: '3%', bottom: '5%', top: '15%', containLabel: true },
            xAxis: {
                type: 'category',
                boundaryGap: false,
                data: data.windows.map(w => `${w}D`),
                axisLabel: { color: '#888' },
                axisLine: { lineStyle: { color: '#333' } }
            },
            yAxis: {
                type: 'value',
                name: 'Volatility (%)',
                scale: true,
                splitLine: { lineStyle: { color: '#333', type: 'dashed' } },
                axisLabel: { color: '#ccc' },
                nameTextStyle: { color: '#ccc' }
            },
            series: [
                {
                    name: 'Max',
                    type: 'line',
                    data: data.max,
                    lineStyle: { opacity: 0 },
                    showSymbol: false
                },
                {
                    name: '75th Pct',
                    type: 'line',
                    data: data.p75,
                    lineStyle: { color: '#4ade80', type: 'dashed' },
                    areaStyle: {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                            offset: 0, color: 'rgba(74, 222, 128, 0.2)'
                        }, {
                            offset: 1, color: 'rgba(74, 222, 128, 0.05)'
                        }])
                    },
                    showSymbol: false
                },
                {
                    name: 'Median',
                    type: 'line',
                    data: data.p50,
                    lineStyle: { color: '#3176B8', width: 2 }, // Blue median
                    showSymbol: true
                },
                {
                    name: '25th Pct',
                    type: 'line',
                    data: data.p25,
                    lineStyle: { color: '#E88B1E', type: 'dashed' },
                    areaStyle: {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                            offset: 0, color: 'rgba(232, 139, 30, 0.2)'
                        }, {
                            offset: 1, color: 'rgba(232, 139, 30, 0.05)'
                        }])
                    },
                    showSymbol: false
                },
                {
                    name: 'Min',
                    type: 'line',
                    data: data.min,
                    lineStyle: { opacity: 0 },
                    showSymbol: false
                },
                {
                    name: 'Current RV',
                    type: 'line',
                    data: data.current_rv,
                    lineStyle: { color: '#ff4444', width: 3 }, // Red thick line
                    itemStyle: { color: '#ff4444' },
                    symbol: 'circle',
                    symbolSize: 8
                }
            ]
        };

        volConeChart.setOption(coneOption);
        volConeChart.hideLoading();
    } catch (e) {
        console.error("Error loading Volatility Cone", e);
        if (volConeChart) volConeChart.hideLoading();
    }
}

function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;

    let csv = [];
    const rows = table.querySelectorAll('tr');

    for (let i = 0; i < rows.length; i++) {
        let row = [], cols = rows[i].querySelectorAll('td, th');

        for (let j = 0; j < cols.length; j++) {
            let data = cols[j].innerText.replace(/(\r\n|\n|\r)/gm, '').replace(/(\s\s)/gm, ' ');
            data = data.replace(/"/g, '""');
            row.push('"' + data + '"');
        }

        if (row.length > 0) {
            csv.push(row.join(','));
        }
    }

    const csvFile = new Blob([csv.join('\n')], { type: 'text/csv' });
    const downloadLink = document.createElement('a');
    downloadLink.download = filename + '.csv';
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = 'none';
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

function exportChartDataToCSV(chartInstance, filename) {
    if (!chartInstance) {
        alert("Chart is not loaded or data is empty.");
        return;
    }

    // Handle Chart.js instances vs ECharts instances
    let isChartJS = typeof chartInstance.config !== 'undefined';
    let isECharts = typeof chartInstance.getOption === 'function';

    if (!isChartJS && !isECharts) {
        alert("Unsupported chart type.");
        return;
    }

    let csvRows = [];
    let headers = ['Date'];
    let seriesNames = [];
    let seriesData = [];
    let xAxisData = [];

    if (isECharts) {
        const option = chartInstance.getOption();
        if (!option) { alert("Error reading chart option"); return; }

        // Find xAxis data
        if (option.xAxis && option.xAxis.length > 0 && option.xAxis[0].data) {
            xAxisData = option.xAxis[0].data;
        } else if (option.xAxis && option.xAxis.length > 1 && option.xAxis[1].data) {
            xAxisData = option.xAxis[1].data;
        } else if (option.dataset && option.dataset.length > 0 && option.dataset[0].source) {
            // dataset fallback
            const src = option.dataset[0].source;
            if (Array.isArray(src) && src.length > 0) {
                // assume first row is headers, first col is dates
                xAxisData = src.slice(1).map(row => row[0]);
            }
        }

        if (option.series && option.series.length > 0) {
            option.series.forEach(s => {
                if (s.name) seriesNames.push(s.name);
                else seriesNames.push('Series');
                seriesData.push(s.data || []);
            });
        }

        // Sometimes dataset source is used alongside series (or exclusively)
        if (seriesData.length === 0 && option.dataset && option.dataset.length > 0 && option.dataset[0].source) {
            const src = option.dataset[0].source;
            if (Array.isArray(src) && src.length > 0) {
                // src[0] is headers, ignore [0][0] which is date
                for (let col = 1; col < src[0].length; col++) {
                    seriesNames.push(src[0][col] || `Series_${col}`);
                    let colData = [];
                    for (let r = 1; r < src.length; r++) {
                        colData.push(src[r][col]);
                    }
                    seriesData.push(colData);
                }
            }
        }

        if (seriesData.length === 0) {
            alert("No series data found in chart");
            return;
        }

        // If still no xAxisData but we have seriesData, just make dummy rows
        if ((!xAxisData || xAxisData.length === 0) && seriesData.length > 0) {
            xAxisData = xAxisData || [];
            let maxLen = 0;
            seriesData.forEach(sd => { if (sd.length > maxLen) maxLen = sd.length; });
            for (let i = 0; i < maxLen; i++) xAxisData.push(`Row_${i}`);
        }
    } else if (isChartJS) {
        const data = chartInstance.data;
        if (!data || !data.datasets || data.datasets.length === 0) return;

        xAxisData = data.labels || [];

        data.datasets.forEach(s => {
            if (s.label) seriesNames.push(s.label);
            else seriesNames.push('Series');
            seriesData.push(s.data || []);
        });
    }

    // Build headers from series names
    seriesNames.forEach(name => {
        headers.push(`"${name}"`);
    });

    csvRows.push(headers.join(','));

    // Build rows
    const len = xAxisData.length > 0 ? xAxisData.length : (seriesData[0] ? seriesData[0].length : 0);

    for (let i = 0; i < len; i++) {
        let row = [];
        if (xAxisData.length > 0) {
            row.push(`"${xAxisData[i]}"`);
        } else {
            row.push(`"Row_${i}"`);
        }

        seriesData.forEach(d => {
            let val = '';
            if (d && d[i] !== undefined) {
                // Handle objects if data is complex (like candlesticks)
                if (typeof d[i] === 'object' && d[i] !== null) {
                    if (d[i].value !== undefined) {
                        val = d[i].value;
                    } else if (Array.isArray(d[i])) {
                        // For Candlesticks [open, close, min, max] or [date, val1, val2]
                        val = d[i].join('|');
                    }
                } else {
                    val = d[i];
                }
            }
            row.push(`"${val}"`);
        });

        csvRows.push(row.join(','));
    }

    const csvFile = new Blob([csvRows.join('\n')], { type: 'text/csv' });
    const downloadLink = document.createElement('a');
    downloadLink.download = filename + '.csv';
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = 'none';
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}
