import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/user_config.dart';

class SyncService extends ChangeNotifier {
  List<Summary> _summaries = [];
  bool _isSyncing = false;
  String? _error;
  DateTime? _lastSyncTime;

  List<Summary> get summaries => _summaries;
  bool get isSyncing => _isSyncing;
  String? get error => _error;
  DateTime? get lastSyncTime => _lastSyncTime;

  Future<bool> sync(UserConfig config) async {
    _isSyncing = true;
    _error = null;
    notifyListeners();

    try {
      final response = await http
          .post(
            Uri.parse('${config.serverUrl}/sync'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'user_id': config.userId,
              'telegram_chat_id': config.telegramChatId,
              'emails': config.emails.map((e) => e.toJson()).toList(),
              'patterns': config.patterns.toJson(),
              'last_sync_time': _lastSyncTime?.toIso8601String(),
            }),
          )
          .timeout(const Duration(seconds: 30));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final summariesList = data['summaries'] as List;

        _summaries = summariesList.map((s) => Summary.fromJson(s)).toList();
        _lastSyncTime = DateTime.now();

        _isSyncing = false;
        notifyListeners();
        return true;
      } else {
        _error = 'Server error: ${response.statusCode}';
      }
    } catch (e) {
      _error = 'Connection failed: ${e.toString()}';
      debugPrint(_error);
    }

    _isSyncing = false;
    notifyListeners();
    return false;
  }

  Future<bool> fetchSummaries(UserConfig config, {int hours = 24}) async {
    try {
      final response = await http
          .get(
            Uri.parse(
              '${config.serverUrl}/summaries/${config.userId}?hours=$hours',
            ),
          )
          .timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as List;
        _summaries = data.map((s) => Summary.fromJson(s)).toList();
        notifyListeners();
        return true;
      }
    } catch (e) {
      _error = 'Failed to fetch summaries: $e';
      debugPrint(_error);
    }
    return false;
  }

  void clearSummaries() {
    _summaries = [];
    notifyListeners();
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}
