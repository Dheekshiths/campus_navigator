from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from utils.graph import CampusGraph
from utils.sms_service import send_sms_notification  
import os
from typing import Dict, Any, Optional

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
campus_graph = CampusGraph()

# Load Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
TWILIO_ENABLED = all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER])

@app.route('/')
def home():
    return render_template('index.html', 
                         nodes=campus_graph.nodes,
                         graph_data={
                             'nodes': campus_graph.nodes,
                             'edges': campus_graph.edges,
                             'path_styles': campus_graph.path_styles
                         })

@app.route('/get_locations', methods=['GET'])
def get_locations():
    """Get all available locations"""
    locations = [{"id": k, "name": v["name"]} for k, v in campus_graph.nodes.items()]
    return jsonify({"locations": locations})

@app.route('/get_path', methods=['POST'])
def get_path() -> Dict[str, Any]:
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Validate required fields
        required_fields = ['start', 'end']
        if not all(field in data for field in required_fields):
            return jsonify({
                "error": "Missing required fields",
                "required": required_fields,
                "received": list(data.keys())
            }), 400

        try:
            start_node = int(data['start'])
            end_node = int(data['end'])
        except ValueError:
            return jsonify({
                "error": "Node IDs must be integers",
                "start_received": data['start'],
                "end_received": data['end']
            }), 400

        # Validate nodes exist
        if start_node not in campus_graph.nodes:
            return jsonify({
                "error": f"Start node {start_node} not found",
                "available_nodes": list(campus_graph.nodes.keys())
            }), 404
            
        if end_node not in campus_graph.nodes:
            return jsonify({
                "error": f"End node {end_node} not found",
                "available_nodes": list(campus_graph.nodes.keys())
            }), 404

        # Find path
        node_path = campus_graph.find_shortest_path(start_node, end_node)
        if not node_path:
            return jsonify({
                "error": "No path found between the selected locations",
                "start_node": start_node,
                "end_node": end_node
            }), 404

        path_details = campus_graph.get_path_details(node_path)
        total_time = campus_graph.calculate_path_time(node_path)
        
        return jsonify({
            "success": True,
            "path": {
                "nodes": node_path,
                "coordinates": path_details,
                "start": campus_graph.nodes[start_node],
                "end": campus_graph.nodes[end_node],
                "estimated_time": f"{total_time:.1f} minutes",
                "path_length": len(node_path)
            },
            "path_styles": campus_graph.path_styles
        })

    except Exception as e:
        app.logger.error(f"Pathfinding error: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "details": str(e)
        }), 500

@app.route('/send_sms', methods=['POST'])
def send_sms() -> Dict[str, Any]:
    """Send SMS with navigation directions."""
    try:
        # Check if Twilio is configured
        if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
            return jsonify({
                "error": "SMS service not configured",
                "details": "Twilio credentials missing"
            }), 503

        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Validate required fields
        required_fields = ['phone', 'path']
        if not all(field in data for field in required_fields):
            return jsonify({
                "error": "Missing required fields",
                "required": required_fields,
                "received": list(data.keys())
            }), 400

        phone_number = data['phone']
        path_data = data['path']

        # Validate phone number format
        if not phone_number.startswith('+'):
            return jsonify({
                "error": "Invalid phone number format",
                "details": "Phone number must include country code (e.g., +1...)"
            }), 400

        # Get start and end node information
        start_node = path_data['start']['node_id'] if isinstance(path_data['start'], dict) else path_data['start']
        end_node = path_data['end']['node_id'] if isinstance(path_data['end'], dict) else path_data['end']
        
        start_name = campus_graph.nodes[start_node]['name']
        end_name = campus_graph.nodes[end_node]['name']

        # Format message
        message = "🚶 Campus Navigation Directions 🚶\n\n"
        message += f"From: {start_name}\nTo: {end_name}\n\n"
        message += "Route:\n"
        
        for i, segment in enumerate(path_data['path_details'], 1):
            if segment.get('type') == 'node':
                continue
            from_name = campus_graph.nodes[segment['from_node']]['name']
            to_name = campus_graph.nodes[segment['to_node']]['name']
            message += f"{i}. {from_name} to {to_name} via {segment['path_type']}\n"
        
        message += f"\nEstimated Time: {path_data['estimated_time']}"

        # Send SMS with correct parameter names
        success = send_sms_notification(
            phone_to=phone_number,
            message=message,
            account_sid=TWILIO_ACCOUNT_SID,
            auth_token=TWILIO_AUTH_TOKEN,
            phone_from=TWILIO_PHONE_NUMBER
        )

        if success:
            return jsonify({
                "status": "success",
                "message": "SMS sent successfully",
                "preview": message
            })
        return jsonify({
            "error": "Failed to send SMS",
            "details": "Check server logs for more information"
        }), 500

    except Exception as e:
        app.logger.error(f"SMS sending error: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)