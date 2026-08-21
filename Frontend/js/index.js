
buttonStartStop = document.getElementById('buttonStartStop');
buttonRestart = document.getElementById('buttonRestart');

async function fetchServerStatus() {
    try{
        const response = await fetch('http://127.0.0.1:8000/status');
        const data = await response.json();
        if(data.status === 'healthy') {
            document.getElementById('serverStatus').textContent = 'Online';
            document.getElementById('serverStatus').style.color = 'var(--status-success)';
            document.getElementById('serverStatusIcon').style.color = 'var(--status-success)';
            document.getElementById('buttonStartStopIcon').classList.remove('fa-play');
            document.getElementById('buttonStartStopIcon').classList.add('fa-stop');
            document.getElementById('buttonStartStopSpan').textContent = 'Stop';
            document.getElementById('buttonStartStop').classList.add('buttonStartStopStop');
        }
        else if(data.status === 'starting') {
            document.getElementById('serverStatus').textContent = 'Starting';
            document.getElementById('serverStatus').style.color = 'var(--status-warning)';
            document.getElementById('serverStatusIcon').style.color = 'var(--status-warning)';
            document.getElementById('buttonStartStopIcon').classList.remove('fa-play');
            document.getElementById('buttonStartStopIcon').classList.add('fa-stop');
            document.getElementById('buttonStartStopSpan').textContent = 'Stop';
            document.getElementById('buttonStartStop').classList.add('buttonStartStopStop');
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
            document.getElementById('buttonStartStopIcon').classList.remove('fa-stop');
            document.getElementById('buttonStartStopIcon').classList.add('fa-play');
            document.getElementById('buttonStartStopSpan').textContent = 'Start';
            document.getElementById('buttonStartStop').classList.remove('buttonStartStopStop');
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

async function fetchServerData() {
    try {
        const response = await fetch('http://127.0.0.1:8000/server/data');
        const data = await response.json();
        if(data.ip){
            document.getElementById('serverInfoHeaderName').textContent = data.serverName;
            document.getElementById('serverVersion').textContent = data.serverVersion;
            document.getElementById('serverIp').textContent = data.ip;
            await fetchServerStatus();
            document.getElementById('serverInfo').classList.remove('serverInfoHidden');
        }
        else{
            document.getElementById('serverInfoHeaderName').textContent = "No Server Found";
            document.getElementById('serverVersion').textContent = "N/A";
            document.getElementById('serverIp').textContent = "N/A";
            document.getElementById('serverInfo').classList.remove('serverInfoHidden');
        }

    }
    catch (error) {
        console.error('Error fetching server data:', error);
    }
}

async function fetchServerStats() {
    try {
        const response = await fetch('http://127.0.0.1:8000/stats');
        const data = await response.json();
        if(data.detail) {
            document.getElementById('serverStatPlayers').textContent = "None";
            document.getElementById('serverStatCPUUsage').textContent = "None";
            document.getElementById('serverStatMemUsage').textContent = "None";
            document.getElementById('serverStatMaxMem').textContent = "None";
            document.getElementById('serverStatUptime').textContent = "None";


        }
        else{
            document.getElementById('serverStatPlayers').textContent = `${data.currentPlayers} / ${data.maxPlayers}`;
            document.getElementById('serverStatCPUUsage').textContent = `${data.cpuUsage}`;
            document.getElementById('serverStatMemUsage').textContent = `${data.currentMemUsage}`;
            document.getElementById('serverStatMaxMem').textContent = `${data.maxMem}`;
            document.getElementById('serverStatUptime').textContent = `${data.uptime}`;
        }
    }

    catch (error) {
        console.error('Error fetching server stats:', error);
    }
}

fetchServerStatus();
fetchServerStats();
fetchServerData();

buttonRestart.addEventListener('click', async() => {
    try {
        const response = await fetch('http://127.0.0.1:8000/server/restart');
        const data = await response.json();
        await fetchServerStatus();
    } catch (error) {
        console.error('Error restarting server:', error);
    }
});

buttonStartStop.addEventListener('click', async() => {
    try {
        const response = await fetch('http://127.0.0.1:8000/server/startstop');
        const data = await response.json();
        await fetchServerStatus();
    } catch (error) {
        console.error('Error starting/stopping server:', error);
    }
});
