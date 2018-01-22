// ============================================================================
// Dumpling visualizers.
// ============================================================================

function dnsDumpling(dumpling) {
    // Display DNS lookup information.

    function lookupDumpling() {
        // Display a single DNS lookup in a div.  The CSS will take care of the
        // display properties (including the transition of the div down the
        // browser window).
        var host_name = dumpling.payload.lookup.hostname;
        var host_div = document.createElement('div');

        var content = document.createTextNode(host_name);
        document.body.appendChild(host_div);
        host_div.appendChild(content);
        host_div.className = 'host-name display';

        // Currently we don't remove the div when we're done with it.  It would
        // make good sense to do so.

        setTimeout(function() {
            // Trigger the CSS transition on the host lookup div.
            host_div.classList.remove('display');
        }, 0);
    }

    if (dumpling.metadata.driver === 'packet') {
        lookupDumpling()
    }
    else {
        // Currently we don't display the interval (summary) dumplings contents.
    }

}

// ----------------------------------------------------------------------------

function packetCountDumpling(dumpling) {
    // Display the packet count dumplings in a table.  Each row displays the
    // network layer name (eg. "TCP") and the number of packets seen in that
    // layer.

    function numberWithCommas(x) {
        // Convert a number like 10000 to 10,000.
        return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }

    var packet_count_container = document.getElementsByClassName(
            'packet-count-container')[0];
    packet_count_container.innerHTML = '';

    // Create the table of per-network-layer packet counts.
    var count_table = document.createElement('table');
    count_table.className = 'packet-counts';
    packet_count_container.appendChild(count_table);

    var sorted_layers = Object.keys(dumpling.payload.packet_counts).sort();

    for (var layer_index in sorted_layers) {
        var layer = sorted_layers[layer_index];
        var layer_row = document.createElement('tr');
        var layer_count = document.createElement('td');
        var layer_name = document.createElement('td');

        layer_count.className = 'layer-count';
        layer_name.className = 'layer-name';
        layer_row.appendChild(layer_count);
        layer_row.appendChild(layer_name);
        count_table.appendChild(layer_row);

        layer_count.textContent = numberWithCommas(
            dumpling.payload.packet_counts[layer]
        );
        layer_name.textContent = layer;
    }
}

// ----------------------------------------------------------------------------

function hubStatusDumpling(dumpling) {
    // Display hub status information.

    var hub_status_container =
        document.getElementsByClassName('hub-status-container')[0];
    hub_status_container.innerHTML = '';
    var status_pre = document.createElement('pre');
    status_pre.className = 'hub-status';
    status_pre.textContent = JSON.stringify(dumpling.payload, null, 2);
    hub_status_container.appendChild(status_pre);
}


// ============================================================================
// Initialization.
// ============================================================================

// Connect to the dumpling hub.
var ws = new WebSocket("ws://localhost:11348/");

ws.onopen = function() {
    // Send the hub our name.  Then we'll start receiving dumplings.
    ws.send("{\"eater_name\": \"webnom\"}");
};

ws.onmessage = function(event) {
    // Convert the JSON dumpling to a JavaScript object.
    var dumpling = JSON.parse(event.data);

    // Send the dumpling to a different handler based on the chef.
    if (dumpling.metadata.chef === "DNSLookupChef") {
        dnsDumpling(dumpling);
    }
    else if (dumpling.metadata.chef === "PacketCountChef") {
        packetCountDumpling(dumpling);
    }
    else if (dumpling.metadata.chef === "SystemStatusChef") {
        hubStatusDumpling(dumpling);
    }
};
