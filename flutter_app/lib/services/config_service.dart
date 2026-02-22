import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';
import 'package:yaml/yaml.dart';
import '../models/user_config.dart';

class ConfigService extends ChangeNotifier {
  UserConfig? _config;
  bool _isLoading = false;
  String? _error;

  UserConfig? get config => _config;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get isLoggedIn => _config != null && _config!.userId.isNotEmpty;

  Future<String> get _configPath async {
    final directory = await getApplicationDocumentsDirectory();
    return '${directory.path}/user_config.yaml';
  }

  Future<void> loadConfig() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final path = await _configPath;
      final file = File(path);

      if (await file.exists()) {
        final contents = await file.readAsString();
        final yaml = loadYaml(contents);
        _config = UserConfig.fromJson(_yamlToMap(yaml));
      }
    } catch (e) {
      _error = 'Failed to load config: $e';
      debugPrint(_error);
    }

    _isLoading = false;
    notifyListeners();
  }

  Future<void> saveConfig(UserConfig config) async {
    _isLoading = true;
    notifyListeners();

    try {
      final path = await _configPath;
      final file = File(path);

      final yamlContent = _toYaml(config.toJson());
      await file.writeAsString(yamlContent);

      _config = config;
      _error = null;
    } catch (e) {
      _error = 'Failed to save config: $e';
      debugPrint(_error);
    }

    _isLoading = false;
    notifyListeners();
  }

  Future<void> logout() async {
    try {
      final path = await _configPath;
      final file = File(path);
      if (await file.exists()) {
        await file.delete();
      }
    } catch (e) {
      debugPrint('Failed to delete config: $e');
    }

    _config = null;
    notifyListeners();
  }

  void updateConfig(UserConfig newConfig) {
    _config = newConfig;
    notifyListeners();
  }

  Map<String, dynamic> _yamlToMap(YamlMap yaml) {
    final map = <String, dynamic>{};
    yaml.forEach((key, value) {
      if (value is YamlList) {
        map[key.toString()] = value.map((e) {
          if (e is YamlMap) {
            return _yamlToMap(e);
          }
          return e;
        }).toList();
      } else if (value is YamlMap) {
        map[key.toString()] = _yamlToMap(value);
      } else {
        map[key.toString()] = value;
      }
    });
    return map;
  }

  String _toYaml(Map<String, dynamic> map, {int indent = 0}) {
    final buffer = StringBuffer();
    final spaces = '  ' * indent;

    map.forEach((key, value) {
      if (value is List) {
        buffer.writeln('$spaces$key:');
        for (final item in value) {
          if (item is Map) {
            buffer.writeln('$spaces  -');
            item.forEach((k, v) {
              buffer.writeln('$spaces    $k: $v');
            });
          } else {
            buffer.writeln('$spaces  - $item');
          }
        }
      } else if (value is Map) {
        buffer.writeln('$spaces$key:');
        buffer.write(_toYaml(value, indent: indent + 1));
      } else {
        buffer.writeln('$spaces$key: $value');
      }
    });

    return buffer.toString();
  }
}
