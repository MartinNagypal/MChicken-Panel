
async function fetchServerStatus() {
    try{
        const response = await fetch('http://127.0.0.1:8000/status');
        const data = await response.json();
        if(data.status === 'healthy') {
            document.getElementById('serverStatus').textContent = 'Online';
            document.getElementById('serverStatus').style.color = 'var(--status-success)';
            document.getElementById('serverStatusIcon').style.color = 'var(--status-success)';
        }
        else if(data.status === 'starting') {
            document.getElementById('serverStatus').textContent = 'Starting';
            document.getElementById('serverStatus').style.color = 'var(--status-warning)';
            document.getElementById('serverStatusIcon').style.color = 'var(--status-warning)';
        }
        else if(data.status === 'unhealthy') {
            document.getElementById('serverStatus').textContent = 'Unhealthy';
            document.getElementById('serverStatus').style.color = 'var(--status-danger)';
            document.getElementById('serverStatusIcon').style.color = 'var(--status-danger)';
        }
        else if(data.status === 'offline') {
            document.getElementById('serverStatus').textContent = 'Offline';
            document.getElementById('serverStatus').style.color = 'var(--status-danger)';
            document.getElementById('serverStatusIcon').style.color = 'var(--status-danger)';
        }
        else{
            document.getElementById('serverStatus').textContent = 'Error';
            document.getElementById('serverStatus').style.color = 'var(--status-danger)';
            document.getElementById('serverStatusIcon').style.color = 'var(--status-danger)';
        }
    }
    catch (error) {
        console.error('Error fetching server status:', error);
    }
}

async function fetchServerStats() {
    try {
        const response = await fetch('http://127.0.0.1:8000/stats');
        const data = await response.json();

        document.getElementById('serverStatPlayers').textContent = `${data.currentPlayers} / ${data.maxPlayers}`;
        document.getElementById('serverStatCPUUsage').textContent = `${data.cpuUsage}`;
        document.getElementById('serverStatMemUsage').textContent = `${data.memUsage}`;
    }

    catch (error) {
        console.error('Error fetching server stats:', error);
    }
}

fetchServerStatus();
fetchServerStats();
