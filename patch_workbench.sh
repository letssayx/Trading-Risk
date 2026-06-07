sed -i 's/<div class="tab-btn" id="main-tab-retail" onclick="switchMainTab('\''retail'\'')">Retail Instruments<\/div>//g' backend/ui/templates/workbench.html
sed -i '/<div id="main-content-retail" class="main-content" style="display: none;">/,/<!-- END RETAIL TAB -->/d' backend/ui/templates/workbench.html

sed -i 's/margin-bottom: 20px;/margin-bottom: 10px;/g' backend/ui/static/css/workbench.css

sed -i 's/<div class="tab-btn" id="main-tab-ai" onclick="switchMainTab('\''ai'\'')">AI Agents<\/div>/<div class="tab-btn" id="main-tab-ai" onclick="switchMainTab('\''ai'\'')">AI Agents<\/div>\n            <div class="tab-btn" id="main-tab-structured" onclick="switchMainTab('\''structured'\'')">Structured Product<\/div>/g' backend/ui/templates/workbench.html

cat << 'INNER' >> backend/ui/templates/workbench.html
    <!-- STRUCTURED PRODUCT TAB -->
    <div id="main-content-structured" class="main-content" style="display: none;">
        <div class="deriv-tabs">
            <button class="deriv-tab-btn active" id="sp-tab-btn-leaps" onclick="switchSPTab('leaps')">Leaps Pricing</button>
        </div>

        <div id="sp-content-leaps" class="deriv-sub-tab active">
            <h2 style="color: white; padding: 20px;">Leaps Pricing Dashboard Coming Soon</h2>
        </div>
    </div>
    <!-- END STRUCTURED PRODUCT TAB -->
INNER

sed -i 's/Market Analysis/Market Activity/g' backend/ui/templates/workbench.html
sed -i 's/Refresh FII Data/Refresh/g' backend/ui/templates/workbench.html
