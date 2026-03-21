
    document.addEventListener("DOMContentLoaded", function() {
        // Link Latest Checkboxes
        let latestCa = document.getElementById("latest-ca-cb");
        let latestBm = document.getElementById("latest-bm-cb");
        if (latestCa && latestBm) {
            latestCa.addEventListener("change", function() { latestBm.checked = this.checked; });
            latestBm.addEventListener("change", function() { latestCa.checked = this.checked; });
        }

        // Link Range Checkboxes
        let rangeCa = document.getElementById("range-ca-cb");
        let rangeBm = document.getElementById("range-bm-cb");
        if (rangeCa && rangeBm) {
            rangeCa.addEventListener("change", function() { rangeBm.checked = this.checked; });
            rangeBm.addEventListener("change", function() { rangeCa.checked = this.checked; });
        }
    });
