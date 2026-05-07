/**
 * DECODE UPLINK: Zamiana bajtów z Taga na obiekt JSON (Serwer otrzymuje dane)
 */
function decodeUplink(input) {
    var data = {};
    var bytes = input.bytes;
    var opcode = bytes[0];

    switch (opcode) {
        case 0x01:
            data.type = "TELEMETRY";
            // Odczyt 4 bajtów (Big-Endian) i zamiana na signed int (obsługa ujemnych koordynatów)
            var rawLat = (bytes[1] << 24) | (bytes[2] << 16) | (bytes[3] << 8) | bytes[4];
            var rawLon = (bytes[5] << 24) | (bytes[6] << 16) | (bytes[7] << 8) | bytes[8];

            data.lat = rawLat / 1000000.0;
            data.lon = rawLon / 1000000.0;
            break;

        case 0x02:
            data.type = "EVENT";
            data.status = "KILLED";
            break;

        case 0x03:
            data.type = "PING";
            break;

        default:
            data.error = "Unknown Opcode: " + opcode;
    }

    return { data: data };
}

/**
 * ENCODE DOWNLINK: Zamiana JSON z serwera na bajty (Tag otrzymuje dane)
 */
function encodeDownlink(input) {
    var bytes = [];
    var data = input.data;

    if (data.cmd === "CONFIG") {
        // 0x01 - CONFIG; team, gameType, timeMinutes, alliesTotal, enemiesTotal, nickname
        bytes.push(0x01);
        bytes.push(data.team & 0xFF);      // 0: RED, 1: BLUE
        bytes.push(data.gameType & 0xFF);

        // Czas gry W MINUTACH (2 bajty, Big-Endian)
        var mins = parseInt(data.timeMinutes) || 0;
        bytes.push((mins >> 8) & 0xFF);
        bytes.push(mins & 0xFF);

        bytes.push(data.alliesTotal & 0xFF);
        bytes.push(data.enemiesTotal & 0xFF);

        // Nickname (znaki ASCII)
        if (data.nickname) {
            for (var i = 0; i < data.nickname.length; i++) {
                bytes.push(data.nickname.charCodeAt(i) & 0xFF);
            }
        }
    }
    else if (data.cmd === "COMMAND") {
        // 0x02 - COMMAND; opcode_cmd
        bytes.push(0x02);
        var cmdMap = {
            "START": 0x10,
            "END": 0x11,
            "WIN_BLUE": 0x12,
            "WIN_RED": 0x13,
            "DIE": 0x14  // Odpowiada CMD_YOU_DIED
        };
        bytes.push(cmdMap[data.val] || 0x00);
    }
    else if (data.cmd === "UPDATE") {
        // 0x03 - UPDATE; allies_alive, enemies_alive
        bytes.push(0x03);
        // Usunięto czas - ramka ma teraz tylko 3 bajty
        bytes.push(data.alliesAlive & 0xFF);
        bytes.push(data.enemiesAlive & 0xFF);
    }

    return { bytes: bytes };
}