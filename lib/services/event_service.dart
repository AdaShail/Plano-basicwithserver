import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:developer' as developer;
import 'auth_service.dart';
import '../config/app_config.dart';

class EventService extends ChangeNotifier {
  static String get baseUrl => AppConfig.getCurrentBaseUrl();

  List<dynamic> _events = [];
  bool _isLoading = false;

  List<dynamic> get events => _events;
  bool get isLoading => _isLoading;

  Future<Map<String, String>> _getHeaders(AuthService authService) async {
    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ${authService.accessToken}',
    };
  }

  Future<Map<String, dynamic>?> createEvent({
    required AuthService authService,
    required String eventType,
    required String startDate,
    String? startTime,
    String? endDate,
    required String location,
    double? budget,
    String? religion,
  }) async {
    try {
      _isLoading = true;
      notifyListeners();

      final response = await http.post(
        Uri.parse('$baseUrl/plan-event'),
        headers: await _getHeaders(authService),
        body: jsonEncode({
          'event_type': eventType,
          'start_date': startDate,
          'start_time': startTime,
          'end_date': endDate,
          'location': location,
          'budget': budget,
          'religion': religion,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        await loadUserEvents(authService); // Refresh events list
        return data;
      } else {
        throw Exception('Failed to create event: ${response.body}');
      }
    } catch (e) {
      developer.log('Create event error: $e', name: 'EventService');
      return null;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // Add new methods to support backend features
  Future<Map<String, dynamic>?> getBudgetExplanation(
    AuthService authService,
    int eventId,
  ) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/events/$eventId/budget/explanation'),
        headers: await _getHeaders(authService),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to fetch budget explanation: ${response.body}');
      }
    } catch (e) {
      developer.log('Get budget explanation error: $e', name: 'EventService');
      return null;
    }
  }

  Future<Map<String, dynamic>?> getTimelineReasoning(
    AuthService authService,
    int eventId,
  ) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/events/$eventId/timeline/reasoning'),
        headers: await _getHeaders(authService),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to fetch timeline reasoning: ${response.body}');
      }
    } catch (e) {
      developer.log('Get timeline reasoning error: $e', name: 'EventService');
      return null;
    }
  }

  Future<Map<String, dynamic>?> getAlternatives(
    AuthService authService,
    int eventId,
  ) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/events/$eventId/alternatives'),
        headers: await _getHeaders(authService),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to fetch alternatives: ${response.body}');
      }
    } catch (e) {
      developer.log('Get alternatives error: $e', name: 'EventService');
      return null;
    }
  }

  Future<void> loadUserEvents(AuthService authService) async {
    try {
      _isLoading = true;
      notifyListeners();

      final response = await http.get(
        Uri.parse('$baseUrl/events'),
        headers: await _getHeaders(authService),
      );

      if (response.statusCode == 200) {
        _events = jsonDecode(response.body);
      } else {
        developer.log(
          'Failed to load events: ${response.body}',
          name: 'EventService',
        );
      }
    } catch (e) {
      developer.log('Load events error: $e', name: 'EventService');
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<Map<String, dynamic>?> getEventDetails(
    AuthService authService,
    int eventId,
  ) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/events/$eventId'),
        headers: await _getHeaders(authService),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to fetch event: ${response.body}');
      }
    } catch (e) {
      developer.log('Get event details error: $e', name: 'EventService');
      return null;
    }
  }

  Future<Map<String, dynamic>?> getDeepDive(
    AuthService authService,
    int eventId,
    int dayNumber,
  ) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/events/$eventId/deep-dive/$dayNumber'),
        headers: await _getHeaders(authService),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to fetch deep dive: ${response.body}');
      }
    } catch (e) {
      developer.log('Get deep dive error: $e', name: 'EventService');
      return null;
    }
  }
}
