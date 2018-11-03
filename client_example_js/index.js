const io = require('socket.io-client');

const socket = io('http://54.161.203.83:80/');

socket.on('user_detection', (data) => {
    console.log(`Received foo: ${JSON.stringify(data)}`);
});




