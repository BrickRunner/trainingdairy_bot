// mcp-server.js (CommonJS)
const express = require('express');
const bodyParser = require('body-parser');
const fs = require('fs');
const { exec } = require('child_process');

const app = express();
app.use(bodyParser.json());

app.post('/mcp', (req, res) => {
    const { tool, input } = req.body;

    try {
        if (tool === 'readFile') {
            const content = fs.readFileSync(input.path, 'utf-8');
            return res.json({ result: content });
        }

        if (tool === 'writeFile') {
            fs.writeFileSync(input.path, input.content, 'utf-8');
            return res.json({ result: 'success' });
        }

        if (tool === 'runTests') {
            exec('pytest tests/', (error, stdout, stderr) => {
                if (error) return res.json({ error: stderr });
                return res.json({ result: stdout });
            });
        }

        res.status(400).json({ error: 'tool_unknown' });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.listen(4000, () => {
    console.log('MCP server running on http://localhost:4000');
});
