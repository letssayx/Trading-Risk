const fs = require('fs');
let content = fs.readFileSync('backend/ui/static/js/script_workbench2.js', 'utf8');

// Replace websocket onmessage block to handle our new output format from step 5 orchestrator
const replacementOnMessage = `            aiWs.onmessage = (event) => {
                const msg = JSON.parse(event.data);

                if (msg.type === "think") {
                    if (!currentQuantLogicBlock) {
                        const id = "quant-logic-" + Date.now();
                        chatFeed.insertAdjacentHTML('beforeend', \`
                        <div class="chat-message deepseek-message" id="\${id}" style="padding: 10px 0; border-bottom: 1px solid #222;">
                            <details open>
                                <summary style="cursor: pointer; color: #64748b; font-weight: bold; margin-bottom: 5px;">[AI] REASONING</summary>
                                <div class="quant-content" style="color: #888; line-height: 1.5; white-space: pre-wrap; padding-left: 20px; font-family: monospace;"></div>
                            </details>
                        </div>\`);
                        currentQuantLogicBlock = document.getElementById(id).querySelector('.quant-content');
                    }
                    currentQuantLogicBlock.insertAdjacentText('beforeend', msg.chunk);

                } else if (msg.type === "stream") {
                    if (!window.currentAnswerBlock) {
                        const id = "final-answer-" + Date.now();
                        chatFeed.insertAdjacentHTML('beforeend', \`
                        <div class="chat-message final-message" id="\${id}" style="padding: 10px 0; border-bottom: 1px solid #222;">
                            <div style="color: #4ade80; font-weight: bold; margin-bottom: 5px;">[AI] ANSWER</div>
                            <div class="answer-content" style="color: #e0e0e0; line-height: 1.5; white-space: pre-wrap;"></div>
                        </div>\`);
                        window.currentAnswerBlock = document.getElementById(id).querySelector('.answer-content');
                    }
                    window.currentAnswerBlock.insertAdjacentText('beforeend', msg.chunk);

                } else if (msg.type === "final") {
                    // Reset current blocks for next message
                    currentQuantLogicBlock = null;
                    window.currentAnswerBlock = null;

                    cmdInput.placeholder = "Type command or symbol (e.g., NIFTY)...";
                    cmdInput.readOnly = false;

                    // Add rating and annotation UI
                    chatFeed.insertAdjacentHTML('beforeend', \`
                        <div class="chat-actions" style="margin-top: 10px; display: flex; gap: 10px; align-items: center; padding-bottom: 15px; border-bottom: 1px solid #333;">
                            <span style="color: #888; font-size: 12px;">Skill Used: \${msg.skill_used} | Trade ID: \${msg.trade_id}</span>
                            <button onclick="rateTrade('\${msg.trade_id}', 1)" style="background: none; border: 1px solid #444; color: #fff; cursor: pointer;">⭐ 1</button>
                            <button onclick="rateTrade('\${msg.trade_id}', 2)" style="background: none; border: 1px solid #444; color: #fff; cursor: pointer;">⭐ 2</button>
                            <button onclick="rateTrade('\${msg.trade_id}', 3)" style="background: none; border: 1px solid #444; color: #fff; cursor: pointer;">⭐ 3</button>
                            <button onclick="rateTrade('\${msg.trade_id}', 4)" style="background: none; border: 1px solid #444; color: #fff; cursor: pointer;">⭐ 4</button>
                            <button onclick="rateTrade('\${msg.trade_id}', 5)" style="background: none; border: 1px solid #444; color: #fff; cursor: pointer;">⭐ 5</button>
                            <button onclick="annotateResponse('\${msg.trade_id}', '\${msg.skill_used}')" style="background: none; border: 1px solid #444; color: #fff; cursor: pointer;">📌 Annotate</button>
                            <input type="text" id="correction-\${msg.trade_id}" placeholder="Correction..." style="background: #111; border: 1px solid #444; color: #fff; padding: 2px 5px;">
                            <button onclick="submitCorrection('\${msg.trade_id}')" style="background: none; border: 1px solid #444; color: #fff; cursor: pointer;">Submit</button>
                        </div>\`);

                    chatFeed.scrollTop = chatFeed.scrollHeight;
                }
            };

            aiWs.onerror = (e) => {
                chatFeed.innerHTML += \`
                <div class="chat-message error-message" style="padding: 10px 0; border-bottom: 1px solid #222;">
                    <div style="color: #b8860b; font-weight: bold; margin-bottom: 5px;">[SYSTEM ERROR]</div>
                    <div class="log-line text-warning">[ERROR] WebSocket connection failed.</div>
                </div>\`;
                cmdInput.placeholder = "Type command or symbol (e.g., NIFTY)...";
                cmdInput.readOnly = false;
            };

            aiWs.onclose = () => {
                cmdInput.placeholder = "Type command or symbol (e.g., NIFTY)...";
                cmdInput.readOnly = false;
            };
        } // END OF runAiAnalysis
`;

const regex = /aiWs\.onmessage = \(event\) => \{[\s\S]*?(?=aiWs\.onerror =|\}\s*?\/\/\s*END OF runAiAnalysis)/m;
content = content.replace(regex, replacementOnMessage);

fs.writeFileSync('backend/ui/static/js/script_workbench2.js', content, 'utf8');
