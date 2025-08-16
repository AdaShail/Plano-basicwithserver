import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../../config/app_config.dart';

class ConnectionTestScreen extends StatefulWidget {
  const ConnectionTestScreen({Key? key}) : super(key: key);

  @override
  State<ConnectionTestScreen> createState() => _ConnectionTestScreenState();
}

class _ConnectionTestScreenState extends State<ConnectionTestScreen> {
  String _status = 'Not tested';
  bool _isLoading = false;
  Map<String, dynamic>? _debugInfo;
  String? _serverResponse;

  @override
  void initState() {
    super.initState();
    _debugInfo = AppConfig.getDebugInfo();
  }

  Future<void> _testConnection() async {
    setState(() {
      _isLoading = true;
      _status = 'Testing...';
      _serverResponse = null;
    });

    try {
      // Test 1: Health check
      final healthUrl = '${AppConfig.getCurrentBaseUrl()}/health';
      final response = await http
          .get(
            Uri.parse(healthUrl),
            headers: {'Content-Type': 'application/json'},
          )
          .timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _status = '✅ Connection successful!';
          _serverResponse = 'Server: ${data['status']} (v${data['version']})';
        });
      } else {
        setState(() {
          _status = '❌ Server error: ${response.statusCode}';
          _serverResponse = response.body;
        });
      }
    } catch (e) {
      setState(() {
        _status = '❌ Connection failed';
        _serverResponse = e.toString();
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _testEventCreation() async {
    setState(() {
      _isLoading = true;
      _status = 'Testing event creation...';
    });

    try {
      final eventUrl = '${AppConfig.getCurrentBaseUrl()}/plan-event';
      final testEvent = {
        'event_type': 'birthday',
        'start_date': '2024-06-15',
        'location': 'Mumbai, India',
        'budget': 25000,
      };

      final response = await http
          .post(
            Uri.parse(eventUrl),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(testEvent),
          )
          .timeout(const Duration(seconds: 30));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _status = '✅ Event creation successful!';
          _serverResponse =
              'Timeline: ${data['timeline']?.length ?? 0} days\n'
              'Budget: ₹${data['estimated_budget'] ?? 'N/A'}';
        });
      } else {
        setState(() {
          _status = '❌ Event creation failed: ${response.statusCode}';
          _serverResponse = response.body;
        });
      }
    } catch (e) {
      setState(() {
        _status = '❌ Event creation error';
        _serverResponse = e.toString();
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Connection Test'),
        backgroundColor: Colors.purple,
        foregroundColor: Colors.white,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Debug Info Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Configuration',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text('URL: ${_debugInfo?['current_url']}'),
                    Text('Platform: ${_debugInfo?['platform']}'),
                    Text(
                      'Environment: ${_debugInfo?['is_production'] == true ? 'Production' : 'Development'}',
                    ),
                    if (_debugInfo?['manual_override'] != null)
                      Text('Override: ${_debugInfo?['manual_override']}'),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 16),

            // Test Buttons
            Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : _testConnection,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blue,
                      foregroundColor: Colors.white,
                    ),
                    child: const Text('Test Connection'),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : _testEventCreation,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green,
                      foregroundColor: Colors.white,
                    ),
                    child: const Text('Test Event API'),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 16),

            // Status Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Text(
                          'Status: ',
                          style: TextStyle(fontWeight: FontWeight.bold),
                        ),
                        if (_isLoading)
                          const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        else
                          Expanded(child: Text(_status)),
                      ],
                    ),
                    if (_serverResponse != null) ...[
                      const SizedBox(height: 8),
                      const Text(
                        'Response:',
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: Colors.grey[100],
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          _serverResponse!,
                          style: const TextStyle(fontFamily: 'monospace'),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),

            const SizedBox(height: 16),

            // Instructions
            const Card(
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Troubleshooting',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    SizedBox(height: 8),
                    Text(
                      '1. Ensure backend server is running on the configured URL',
                    ),
                    Text('2. Check firewall and network connectivity'),
                    Text(
                      '3. For physical devices, use your computer\'s IP address',
                    ),
                    Text('4. Verify CORS is enabled in the backend'),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
