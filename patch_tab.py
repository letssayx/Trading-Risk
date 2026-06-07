import re

with open('./backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

search_pattern = """        <!-- TAB CRYPTO -->
        <div id="tab-crypto" class="main-tab-content">
            <div style="padding: 20px; text-align: center; color: #888; font-size: 1.2em; height: 100%; display: flex; align-items: center; justify-content: center;">
                Crypto module is under construction...
            </div>
        </div>

        <!-- TAB RETAIL INSTRUMENTS -->
        <div id="tab-retail_instruments" class="main-tab-content">
            <div style="padding: 20px; text-align: center; color: #888; font-size: 1.2em; height: 100%; display: flex; align-items: center; justify-content: center;">
                Retail Instruments module is under construction...
            </div>
        </div>"""

replace_block = """        <!-- TAB CRYPTO -->
        <div id="tab-crypto" class="main-tab-content">
            <div style="padding: 20px; text-align: center; color: #888; font-size: 1.2em; height: 100%; display: flex; align-items: center; justify-content: center;">
                Crypto module is under construction...
            </div>
        </div>

        <!-- TAB STRUCTURED PRODUCT -->
        <div id="tab-structured_product" class="main-tab-content" style="overflow: hidden; display: flex; flex-direction: column;">
            <!-- Structured Product Sub-Tabs Bar -->
            <div class="deriv-tabs-bar" style="display: flex; background: #1e1e1e; border-bottom: 1px solid #333; overflow-x: auto; flex-shrink: 0;">
                <div class="wb-tab active" id="sp-tab-btn-leaps" onclick="switchSPTab('leaps')" style="padding: 8px 15px; cursor: pointer; border-bottom: 2px solid #60a5fa; color: #60a5fa; white-space: nowrap;">Leaps Pricing</div>
            </div>

            <!-- Structured Product Sub-Tabs Content Container -->
            <div style="flex: 1; overflow-y: auto; background: #121212; position: relative;" id="sp-tabs-container">
                <!-- SUB-TAB Leaps Pricing -->
                <div id="sp-tab-leaps" class="sp-sub-tab" style="padding: 20px; height: 100%; overflow-y: auto; display: flex; flex-direction: column; gap: 20px;">
                    <div style="padding: 20px; text-align: center; color: #888; font-size: 1.2em; height: 100%; display: flex; align-items: center; justify-content: center;">
                        Leaps Pricing module is under construction...
                    </div>
                </div>
            </div>
        </div>"""

content = content.replace(search_pattern, replace_block)

with open('./backend/ui/templates/workbench.html', 'w') as f:
    f.write(content)
