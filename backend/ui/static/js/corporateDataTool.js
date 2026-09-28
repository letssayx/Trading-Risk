const CorporateDataTool = {
    async fetchAndRenderCorporateActions() {
        const tbody = document.getElementById('corporate-actions-tbody');
        if(!tbody) return;
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:#888;">Fetching Corporate Actions...</td></tr>';
        try {
            const response = await fetch('/api/data/corporate_actions?days=30');
            const data = await response.json();
            if(!data || data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:#888;">No Corporate Actions found.</td></tr>';
                return;
            }
            tbody.innerHTML = data.map(action => `
                <tr>
                    <td style="padding: 10px 8px;">${action.symbol || '-'}</td>
                    <td style="padding: 10px 8px;">${action.company_name || '-'}</td>
                    <td style="padding: 10px 8px;">${action.purpose || '-'}</td>
                    <td style="padding: 10px 8px;">${action.ex_date || '-'}</td>
                    <td style="padding: 10px 8px;">${action.record_date || '-'}</td>
                    <td style="padding: 10px 8px;">${action.bc_start_date || '-'}</td>
                    <td style="padding: 10px 8px;">${action.bc_end_date || '-'}</td>
                </tr>
            `).join('');
        } catch (e) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:red;">Error fetching actions: ${e.message}</td></tr>`;
        }
    },

    async fetchAndRenderAnnouncements() {
        const tbody = document.getElementById('corporate-announcements-tbody');
        if(!tbody) return;
        tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:#888;">Fetching Announcements...</td></tr>';
        try {
            const response = await fetch('/api/data/corporate_announcements?days=30');
            const data = await response.json();
            if(!data || data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:#888;">No Announcements found.</td></tr>';
                return;
            }
            tbody.innerHTML = data.map(ann => `
                <tr>
                    <td style="padding: 10px 8px;">${ann.symbol || '-'}</td>
                    <td style="padding: 10px 8px;">${ann.broadcast_date || '-'}</td>
                    <td style="padding: 10px 8px;">${ann.subject || '-'}</td>
                    <td style="padding: 10px 8px;">
                        ${ann.attachment_url ? `<a href="${ann.attachment_url}" target="_blank" style="color: #60a5fa;">View PDF</a>` : '-'}
                    </td>
                </tr>
            `).join('');
        } catch (e) {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:red;">Error fetching announcements: ${e.message}</td></tr>`;
        }
    }
};

window.CorporateDataTool = CorporateDataTool;
