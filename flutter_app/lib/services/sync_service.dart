import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/user_config.dart';

/// Error types for network failures
enum SyncErrorType {
  noInternet,
  timeout,
  serverError,
  invalidResponse,
  unknown,
}

/// Detailed error information for sync operations
class SyncError {
  final SyncErrorType type;
  final String message;
  final int? statusCode;

  SyncError({
    required this.type,
    required this.message,
    this.statusCode,
  });

  @override
  String toString() => message;

  /// Get a user-friendly error message
  String get userMessage {
    switch (type) {
      case SyncErrorType.noInternet:
        return 'No internet connection. Please check your network.';
      case SyncErrorType.timeout:
        return 'Connection timed out. Server may be busy.';
      case SyncErrorType.serverError:
        return 'Server error (${statusCode ?? 500}). Please try again.';
      case SyncErrorType.invalidResponse:
        return 'Invalid response from server.';
      case SyncErrorType.unknown:
        return 'An unexpected error occurred.';
    }
  }

  /// Get an icon suggestion for the error type
  String get icon {
    switch (type) {
      case SyncErrorType.noInternet:
        return 'wifi_off';
      case SyncErrorType.timeout:
        return 'timer_off';
      case SyncErrorType.serverError:
        return 'error';
      case SyncErrorType.invalidResponse:
        return 'warning';
      case SyncErrorType.unknown:
        return 'help';
    }
  }
}

class SyncService extends ChangeNotifier {
  List<Summary> _summaries = [];
  bool _isSyncing = false;
  SyncError? _syncError;
  DateTime? _lastSyncTime;
  int _retryCount = 0;
  static const int maxRetries = 3;

  List<Summary> get summaries => _summaries;
  bool get isSyncing => _isSyncing;
  SyncError? get error => _syncError;
  DateTime? get lastSyncTime => _lastSyncTime;
  int get retryCount => _retryCount;

  /// Check if server is reachable
  Future<bool> checkConnection(String serverUrl) async {
    try {
      final response = await http
          .get(Uri.parse('$serverUrl/health'))
          .timeout(const Duration(seconds: 5));
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  /// Classify error type from exception
  SyncErrorType _classifyError(dynamic error) {
    if (error is SocketException ||
        (error is http.ClientException &&
            error.toString().toLowerCase().contains('network'))) {
      return SyncErrorType.noInternet;
    } else if (error is TimeoutException ||
        (error is http.ClientException &&
            error.toString().toLowerCase().contains('timeout'))) {
      return SyncErrorType.timeout;
    } else if (error is FormatException ||
        (error is http.ClientException &&
            error.toString().toLowerCase().contains('invalid'))) {
      return SyncErrorType.invalidResponse;
    }
    return SyncErrorType.unknown;
  }

  Future<bool> sync(UserConfig config) async {
    _isSyncing = true;
    _syncError = null;
    notifyListeners();

    try {
      // Validate server URL
      if (!config.serverUrl.startsWith('http://') &&
          !config.serverUrl.startsWith('https://')) {
        _syncError = SyncError(
          type: SyncErrorType.unknown,
          message: 'Invalid server URL. Must start with http:// or https://',
        );
        _isSyncing = false;
        notifyListeners();
        return false;
      }

      final syncData = {
        'user_id': config.userId,
        'telegram_chat_id': config.telegramChatId,
        'emails': config.emails.map((e) => e.toJson()).toList(),
        'patterns': config.patterns.toJson(),
        'last_sync_time': _lastSyncTime?.toIso8601String(),
      };

      debugPrint('🔄 Syncing config for user: ${config.userId}');
      debugPrint('📡 Server: ${config.serverUrl}');

      final response = await http
          .post(
            Uri.parse('${config.serverUrl}/sync'),
            headers: {
              'Content-Type': 'application/json',
              'User-Agent': 'MailAgent-Mobile/2.0',
            },
            body: jsonEncode(syncData),
          )
          .timeout(
            const Duration(seconds: 30),
            onTimeout: () {
              throw TimeoutException('Request timed out after 30 seconds');
            },
          );

      debugPrint('📥 Response status: ${response.statusCode}');

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final summariesList = data['summaries'] as List;

        _summaries = summariesList.map((s) => Summary.fromJson(s)).toList();
        _lastSyncTime = DateTime.now();
        _retryCount = 0;

        debugPrint('✅ Sync successful. Found ${_summaries.length} summaries.');

        _isSyncing = false;
        notifyListeners();
        return true;
      } else if (response.statusCode >= 500) {
        // Server error - might be temporary
        _syncError = SyncError(
          type: SyncErrorType.serverError,
          message: 'Server error: ${response.statusCode}. ${response.reasonPhrase}',
          statusCode: response.statusCode,
        );
        debugPrint('❌ Server error: ${response.statusCode}');
      } else if (response.statusCode == 400) {
        // Bad request - client error
        final errorData = jsonDecode(response.body);
        _syncError = SyncError(
          type: SyncErrorType.invalidResponse,
          message: 'Invalid config: ${errorData['detail'] ?? 'Unknown error'}',
          statusCode: response.statusCode,
        );
        debugPrint('❌ Bad request: ${response.body}');
      } else {
        // Other errors
        _syncError = SyncError(
          type: SyncErrorType.serverError,
          message: 'Unexpected response: ${response.statusCode}',
          statusCode: response.statusCode,
        );
      }
    } on SocketException catch (e) {
      _syncError = SyncError(
        type: SyncErrorType.noInternet,
        message: 'No internet connection. Please check your network settings.',
      );
      debugPrint('❌ Network error: ${e.message}');
    } on TimeoutException catch (e) {
      _syncError = SyncError(
        type: SyncErrorType.timeout,
        message: 'Connection timed out. Server may be busy or unreachable.',
      );
      debugPrint('❌ Timeout: ${e.message}');
    } on FormatException catch (e) {
      _syncError = SyncError(
        type: SyncErrorType.invalidResponse,
        message: 'Invalid response format from server.',
      );
      debugPrint('❌ Format error: ${e.message}');
    } catch (e) {
      _syncError = SyncError(
        type: _classifyError(e),
        message: 'Connection failed: ${e.toString()}',
      );
      debugPrint('❌ Unexpected error: ${e.toString()}');
    }

    _isSyncing = false;
    notifyListeners();
    return false;
  }

  /// Sync with automatic retry on failure
  Future<bool> syncWithRetry(UserConfig config) async {
    _retryCount = 0;

    while (_retryCount < maxRetries) {
      final success = await sync(config);
      if (success) {
        return true;
      }

      _retryCount++;
      debugPrint('🔄 Retry attempt $_retryCount/$maxRetries');

      if (_retryCount < maxRetries) {
        // Wait before retry (exponential backoff)
        await Future.delayed(Duration(seconds: 2 * _retryCount));
      }
    }

    debugPrint('❌ All retry attempts failed');
    return false;
  }

  Future<bool> fetchSummaries(UserConfig config, {int hours = 24}) async {
    _syncError = null;

    try {
      // Validate server URL
      if (!config.serverUrl.startsWith('http://') &&
          !config.serverUrl.startsWith('https://')) {
        _syncError = SyncError(
          type: SyncErrorType.unknown,
          message: 'Invalid server URL',
        );
        return false;
      }

      final url =
          '${config.serverUrl}/summaries/${config.userId}?hours=$hours';
      debugPrint('📥 Fetching summaries from: $url');

      final response = await http
          .get(
            Uri.parse(url),
            headers: {'User-Agent': 'MailAgent-Mobile/2.0'},
          )
          .timeout(
            const Duration(seconds: 10),
            onTimeout: () {
              throw TimeoutException('Request timed out after 10 seconds');
            },
          );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as List;
        _summaries = data.map((s) => Summary.fromJson(s)).toList();
        debugPrint('✅ Fetched ${_summaries.length} summaries');
        notifyListeners();
        return true;
      } else {
        _syncError = SyncError(
          type: SyncErrorType.serverError,
          message: 'Server error: ${response.statusCode}',
          statusCode: response.statusCode,
        );
        return false;
      }
    } on SocketException catch (e) {
      _syncError = SyncError(
        type: SyncErrorType.noInternet,
        message: 'No internet connection',
      );
      debugPrint('❌ Network error: ${e.message}');
      return false;
    } on TimeoutException catch (e) {
      _syncError = SyncError(
        type: SyncErrorType.timeout,
        message: 'Request timed out',
      );
      debugPrint('❌ Timeout: ${e.message}');
      return false;
    } catch (e) {
      _syncError = SyncError(
        type: _classifyError(e),
        message: 'Failed to fetch summaries: ${e.toString()}',
      );
      debugPrint('❌ Error: ${e.toString()}');
      return false;
    }
  }

  void clearSummaries() {
    _summaries = [];
    notifyListeners();
  }

  void clearError() {
    _syncError = null;
    notifyListeners();
  }

  void resetRetryCount() {
    _retryCount = 0;
    notifyListeners();
  }
}
