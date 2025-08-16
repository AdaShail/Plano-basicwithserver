import 'dart:io';
import 'package:flutter/foundation.dart';

class AppConfig {
  // Backend Configuration URLs
  static const String _localhostUrl = 'http://localhost:8000'; // Main Server
  static const String _androidEmulatorUrl = 'http://10.0.2.2:8000';
  static const String _iosSimulatorUrl = 'http://localhost:8000';

  // Production URL (update this for production deployment)
  static const String _productionUrl = 'https://your-domain.com';

  // Get the appropriate URL based on platform and environment
  static String getBaseUrl() {
    // For web platform, always use localhost
    if (kIsWeb) {
      return _localhostUrl;
    }

    // For mobile platforms, detect emulator vs physical device
    if (Platform.isAndroid) {
      // Android emulator uses 10.0.2.2 to reach host machine
      return _androidEmulatorUrl;
    } else if (Platform.isIOS) {
      // iOS simulator can use localhost or 127.0.0.1
      return _iosSimulatorUrl;
    }

    // Default to localhost for desktop platforms
    return _localhostUrl;
  }

  // Manual override for physical device testing
  // Call this method with your computer's IP address
  static String? _manualBaseUrl;

  static void setManualBaseUrl(String url) {
    _manualBaseUrl = url;
  }

  static String getCurrentBaseUrl() {
    return _manualBaseUrl ?? getBaseUrl();
  }

  // API Endpoints
  static const String planEventEndpoint = '/plan-event';
  static const String eventsEndpoint = '/events';
  static const String healthEndpoint = '/health';

  // Environment detection
  static bool get isProduction => _manualBaseUrl?.contains('https') ?? false;
  static bool get isDevelopment => !isProduction;

  // Debug information
  static Map<String, dynamic> getDebugInfo() {
    return {
      'current_url': getCurrentBaseUrl(),
      'platform': _getPlatformName(),
      'is_web': kIsWeb,
      'is_production': isProduction,
      'manual_override': _manualBaseUrl,
    };
  }

  static String _getPlatformName() {
    if (kIsWeb) return 'Web';
    if (Platform.isAndroid) return 'Android';
    if (Platform.isIOS) return 'iOS';
    if (Platform.isMacOS) return 'macOS';
    if (Platform.isWindows) return 'Windows';
    if (Platform.isLinux) return 'Linux';
    return 'Unknown';
  }
}
