import re
with open("backend/ui/static/js/mwplTool.js", "r") as f:
    text = f.read()

# Replace the catch block to finally
old_end = """        } catch (e) {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:red;">Error: ${e.message}</td></tr>`;
        }

        if (loadBtn) {
            loadBtn.disabled = false;
            loadBtn.innerHTML = originalText;
        }
    }"""

new_end = """        } catch (e) {
            console.error("Failed to load MWPL Analysis", e);
            tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:#f48771;">Error loading data: ${e.message}</td></tr>`;
        } finally {
            if (loadBtn) {
                loadBtn.innerHTML = originalText;
                loadBtn.disabled = false;
            }
        }
    }"""

text = text.replace(old_end, new_end)
with open("backend/ui/static/js/mwplTool.js", "w") as f:
    f.write(text)
