const http = require('http');
const url = require('url');
const CDP = require('chrome-remote-interface');

let client;
let frameId;

async function connectDebugger(wsUrl) {
    try {
        client = await CDP({ target: wsUrl });
        const { Debugger } = client;
        await Debugger.enable();

        client.Debugger.paused(({ callFrames }) => {
            console.log('Debugger paused at:');
            callFrames.forEach((frame, index) => {
                console.log(`#${index}: ${frame.functionName} (${frame.url}:${frame.location.lineNumber}:${frame.location.columnNumber})`);
            });

            if (callFrames.length > 0) {
                frameId = callFrames[0].callFrameId;
                console.log('Frame ID set for evaluation:', frameId);
            }
        });

        process.stdin.resume();
    } catch (err) {
        console.error('Error connecting to debugger:', err);
    }
}

async function evaluateExpression(res, expression) {
    if (!client || !frameId) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Debugger not connected or paused frame not available' }));
        return;
    }

    try {
        const { Debugger } = client;
        const evaluationResponse = await Debugger.evaluateOnCallFrame({
            callFrameId: frameId,
            expression: expression
        });

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ result: evaluationResponse.result }));
    } catch (err) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Error evaluating expression', details: err.message }));
    }
}

const server = http.createServer((req, res) => {
    const parsedUrl = url.parse(req.url, true);
    const pathname = parsedUrl.pathname;

    if (req.method === 'POST' && pathname === '/connect') {
        let body = '';
        req.on('data', chunk => {
            body += chunk.toString();
        });
        req.on('end', () => {
            const { wsUrl } = JSON.parse(body);
            if (!wsUrl) {
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: 'WebSocket URL is required' }));
                return;
            }

            connectDebugger(wsUrl).then(() => {
                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ message: 'Debugger connected' }));
            });
        });
    } else if (req.method === 'POST' && pathname === '/evaluate') {
        let body = '';
        req.on('data', chunk => {
            body += chunk.toString();
        });
        req.on('end', () => {
            const { expression } = JSON.parse(body);
            if (!expression) {
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: 'Expression is required' }));
                return;
            }

            evaluateExpression(res, expression);
        });
    } else {
        res.writeHead(404, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Not Found' }));
    }
});

server.listen(3000, () => {
    console.log('Server running on port 3000');
});

process.on('SIGINT', async () => {
    console.log('Closing client connection...');
    if (client) {
        await client.close();
    }
    server.close(() => {
        console.log('Server closed');
        process.exit(0);
    });
});