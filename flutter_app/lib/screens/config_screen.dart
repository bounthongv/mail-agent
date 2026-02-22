import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import '../services/config_service.dart';
import '../services/sync_service.dart';
import '../models/user_config.dart';

class ConfigScreen extends StatefulWidget {
  const ConfigScreen({super.key});

  @override
  State<ConfigScreen> createState() => _ConfigScreenState();
}

class _ConfigScreenState extends State<ConfigScreen> {
  final _telegramController = TextEditingController();
  List<EmailAccount> _emails = [];
  List<String> _trustedSenders = [];
  List<String> _spamKeywords = [];
  List<String> _deleteKeywords = [];
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _loadConfig();
  }

  void _loadConfig() {
    final config = context.read<ConfigService>().config;
    if (config != null) {
      _telegramController.text = config.telegramChatId;
      _emails = List.from(config.emails);
      _trustedSenders = List.from(config.patterns.trustedSenders);
      _spamKeywords = List.from(config.patterns.spamKeywords);
      _deleteKeywords = List.from(config.patterns.deleteKeywords);
    }
  }

  Future<void> _saveAndSync() async {
    setState(() => _isLoading = true);

    final configService = context.read<ConfigService>();
    final syncService = context.read<SyncService>();

    final newConfig = UserConfig(
      userId: configService.config?.userId ?? '',
      telegramChatId: _telegramController.text.trim(),
      emails: _emails,
      patterns: PatternConfig(
        trustedSenders: _trustedSenders,
        spamKeywords: _spamKeywords,
        deleteKeywords: _deleteKeywords,
      ),
      serverUrl: configService.config?.serverUrl ?? 'http://localhost:8000',
    );

    await configService.saveConfig(newConfig);
    await syncService.sync(newConfig);

    setState(() => _isLoading = false);

    if (mounted) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Config saved and synced!')));
    }
  }

  void _addEmailAccount() {
    showDialog(
      context: context,
      builder: (context) => _AddEmailDialog(
        onAdd: (email, password, host, port) {
          setState(() {
            _emails.add(
              EmailAccount(
                email: email,
                password: password,
                imapHost: host,
                imapPort: port,
              ),
            );
          });
        },
      ),
    );
  }

  void _removeEmail(int index) {
    setState(() {
      _emails.removeAt(index);
    });
  }

  void _editPatterns(
    String title,
    List<String> patterns,
    Function(List<String>) onSave,
  ) {
    showDialog(
      context: context,
      builder: (context) =>
          _PatternDialog(title: title, patterns: patterns, onSave: onSave),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Configuration'),
        actions: [
          if (_isLoading)
            const Center(
              child: Padding(
                padding: EdgeInsets.all(16),
                child: SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
              ),
            )
          else
            TextButton.icon(
              onPressed: _saveAndSync,
              icon: const Icon(Icons.save),
              label: const Text('Save & Sync'),
            ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _buildSectionHeader('Telegram'),
          TextField(
            controller: _telegramController,
            decoration: InputDecoration(
              labelText: 'Telegram Chat ID',
              hintText: 'Get from @userinfobot',
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            keyboardType: TextInputType.number,
          ),

          const SizedBox(height: 24),
          _buildSectionHeader('Email Accounts'),
          ..._emails.asMap().entries.map((entry) {
            final index = entry.key;
            final email = entry.value;
            return Card(
              child: ListTile(
                leading: const Icon(Icons.email),
                title: Text(email.email),
                subtitle: Text('${email.imapHost}:${email.imapPort}'),
                trailing: IconButton(
                  icon: const Icon(Icons.delete, color: Colors.red),
                  onPressed: () => _removeEmail(index),
                ),
              ),
            );
          }),
          const SizedBox(height: 8),
          OutlinedButton.icon(
            onPressed: _addEmailAccount,
            icon: const Icon(Icons.add),
            label: const Text('Add Email Account'),
          ),

          const SizedBox(height: 24),
          _buildSectionHeader('Patterns'),
          _buildPatternTile('Trusted Senders', _trustedSenders, (p) {
            setState(() => _trustedSenders = p);
          }),
          _buildPatternTile('Spam Keywords', _spamKeywords, (p) {
            setState(() => _spamKeywords = p);
          }),
          _buildPatternTile('Delete Keywords', _deleteKeywords, (p) {
            setState(() => _deleteKeywords = p);
          }),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Text(
        title,
        style: GoogleFonts.inter(fontSize: 18, fontWeight: FontWeight.bold),
      ),
    );
  }

  Widget _buildPatternTile(
    String title,
    List<String> patterns,
    Function(List<String>) onSave,
  ) {
    return Card(
      child: ListTile(
        leading: const Icon(Icons.filter_list),
        title: Text(title),
        subtitle: Text('${patterns.length} patterns'),
        trailing: const Icon(Icons.edit),
        onTap: () => _editPatterns(title, List.from(patterns), (newPatterns) {
          onSave(newPatterns);
          Navigator.pop(context);
        }),
      ),
    );
  }
}

class _AddEmailDialog extends StatefulWidget {
  final Function(String, String, String, int) onAdd;

  const _AddEmailDialog({required this.onAdd});

  @override
  State<_AddEmailDialog> createState() => _AddEmailDialogState();
}

class _AddEmailDialogState extends State<_AddEmailDialog> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _hostController = TextEditingController(text: 'imap.gmail.com');
  final _portController = TextEditingController(text: '993');

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Add Email Account'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: _emailController,
              decoration: const InputDecoration(labelText: 'Email'),
            ),
            TextField(
              controller: _passwordController,
              decoration: const InputDecoration(labelText: 'App Password'),
              obscureText: true,
            ),
            TextField(
              controller: _hostController,
              decoration: const InputDecoration(labelText: 'IMAP Host'),
            ),
            TextField(
              controller: _portController,
              decoration: const InputDecoration(labelText: 'IMAP Port'),
              keyboardType: TextInputType.number,
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: () {
            widget.onAdd(
              _emailController.text.trim(),
              _passwordController.text,
              _hostController.text.trim(),
              int.tryParse(_portController.text) ?? 993,
            );
            Navigator.pop(context);
          },
          child: const Text('Add'),
        ),
      ],
    );
  }
}

class _PatternDialog extends StatefulWidget {
  final String title;
  final List<String> patterns;
  final Function(List<String>) onSave;

  const _PatternDialog({
    required this.title,
    required this.patterns,
    required this.onSave,
  });

  @override
  State<_PatternDialog> createState() => _PatternDialogState();
}

class _PatternDialogState extends State<_PatternDialog> {
  late List<String> _patterns;
  final _controller = TextEditingController();

  @override
  void initState() {
    super.initState();
    _patterns = List.from(widget.patterns);
  }

  void _addPattern() {
    if (_controller.text.trim().isNotEmpty) {
      setState(() {
        _patterns.add(_controller.text.trim());
        _controller.clear();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(widget.title),
      content: SizedBox(
        width: double.maxFinite,
        height: 400,
        child: Column(
          children: [
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    decoration: const InputDecoration(
                      hintText: 'Enter pattern',
                    ),
                    onSubmitted: (_) => _addPattern(),
                  ),
                ),
                IconButton(icon: const Icon(Icons.add), onPressed: _addPattern),
              ],
            ),
            const SizedBox(height: 8),
            Expanded(
              child: ListView.builder(
                itemCount: _patterns.length,
                itemBuilder: (context, index) {
                  return ListTile(
                    title: Text(_patterns[index]),
                    trailing: IconButton(
                      icon: const Icon(Icons.delete, size: 20),
                      onPressed: () {
                        setState(() => _patterns.removeAt(index));
                      },
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: () => widget.onSave(_patterns),
          child: const Text('Save'),
        ),
      ],
    );
  }
}
