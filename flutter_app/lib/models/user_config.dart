class EmailAccount {
  final String email;
  final String password;
  final String imapHost;
  final int imapPort;
  final bool enabled;

  EmailAccount({
    required this.email,
    required this.password,
    this.imapHost = 'imap.gmail.com',
    this.imapPort = 993,
    this.enabled = true,
  });

  factory EmailAccount.fromJson(Map<String, dynamic> json) {
    return EmailAccount(
      email: json['email'] ?? '',
      password: json['password'] ?? '',
      imapHost: json['imap_host'] ?? 'imap.gmail.com',
      imapPort: json['imap_port'] ?? 993,
      enabled: json['enabled'] ?? true,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'email': email,
      'password': password,
      'imap_host': imapHost,
      'imap_port': imapPort,
      'enabled': enabled,
    };
  }

  EmailAccount copyWith({
    String? email,
    String? password,
    String? imapHost,
    int? imapPort,
    bool? enabled,
  }) {
    return EmailAccount(
      email: email ?? this.email,
      password: password ?? this.password,
      imapHost: imapHost ?? this.imapHost,
      imapPort: imapPort ?? this.imapPort,
      enabled: enabled ?? this.enabled,
    );
  }
}

class PatternConfig {
  final List<String> trustedSenders;
  final List<String> spamKeywords;
  final List<String> deleteKeywords;

  PatternConfig({
    this.trustedSenders = const [],
    this.spamKeywords = const [],
    this.deleteKeywords = const [],
  });

  factory PatternConfig.fromJson(Map<String, dynamic> json) {
    return PatternConfig(
      trustedSenders: List<String>.from(json['trusted_senders'] ?? []),
      spamKeywords: List<String>.from(json['spam_keywords'] ?? []),
      deleteKeywords: List<String>.from(json['delete_keywords'] ?? []),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'trusted_senders': trustedSenders,
      'spam_keywords': spamKeywords,
      'delete_keywords': deleteKeywords,
    };
  }
}

class UserConfig {
  final String userId;
  final String telegramChatId;
  final List<EmailAccount> emails;
  final PatternConfig patterns;
  final String serverUrl;

  UserConfig({
    required this.userId,
    this.telegramChatId = '',
    this.emails = const [],
    this.patterns = const PatternConfig(),
    this.serverUrl = 'http://localhost:8000',
  });

  factory UserConfig.fromJson(Map<String, dynamic> json) {
    return UserConfig(
      userId: json['user_id'] ?? '',
      telegramChatId: json['telegram_chat_id'] ?? '',
      emails:
          (json['emails'] as List<dynamic>?)
              ?.map((e) => EmailAccount.fromJson(e))
              .toList() ??
          [],
      patterns: json['patterns'] != null
          ? PatternConfig.fromJson(json['patterns'])
          : const PatternConfig(),
      serverUrl: json['server_url'] ?? 'http://localhost:8000',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'user_id': userId,
      'telegram_chat_id': telegramChatId,
      'emails': emails.map((e) => e.toJson()).toList(),
      'patterns': patterns.toJson(),
      'server_url': serverUrl,
    };
  }

  UserConfig copyWith({
    String? userId,
    String? telegramChatId,
    List<EmailAccount>? emails,
    PatternConfig? patterns,
    String? serverUrl,
  }) {
    return UserConfig(
      userId: userId ?? this.userId,
      telegramChatId: telegramChatId ?? this.telegramChatId,
      emails: emails ?? this.emails,
      patterns: patterns ?? this.patterns,
      serverUrl: serverUrl ?? this.serverUrl,
    );
  }
}

class Summary {
  final int id;
  final String sender;
  final String subject;
  final String summaryText;
  final DateTime receivedAt;
  final DateTime createdAt;

  Summary({
    required this.id,
    required this.sender,
    required this.subject,
    required this.summaryText,
    required this.receivedAt,
    required this.createdAt,
  });

  factory Summary.fromJson(Map<String, dynamic> json) {
    return Summary(
      id: json['id'],
      sender: json['sender'] ?? 'Unknown',
      subject: json['subject'] ?? 'No Subject',
      summaryText: json['summary_text'] ?? '',
      receivedAt: DateTime.parse(json['received_at']),
      createdAt: DateTime.parse(json['created_at']),
    );
  }
}
