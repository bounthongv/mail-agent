import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import 'package:pull_to_refresh/pull_to_refresh.dart';
import '../services/config_service.dart';
import '../services/sync_service.dart';
import '../models/user_config.dart';
import 'config_screen.dart';
import 'login_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final RefreshController _refreshController = RefreshController();

  /// Get icon for error type
  IconData _getErrorIcon(SyncErrorType type) {
    switch (type) {
      case SyncErrorType.noInternet:
        return Icons.wifi_off_outlined;
      case SyncErrorType.timeout:
        return Icons.timer_off_outlined;
      case SyncErrorType.serverError:
        return Icons.error_outline;
      case SyncErrorType.invalidResponse:
        return Icons.warning_amber_outlined;
      case SyncErrorType.unknown:
        return Icons.help_outline;
    }
  }

  @override
  void initState() {
    super.initState();
    _autoSync();
  }

  Future<void> _autoSync() async {
    final configService = context.read<ConfigService>();
    final syncService = context.read<SyncService>();

    if (configService.config != null) {
      await syncService.sync(configService.config!);
    }
  }

  Future<void> _onRefresh() async {
    final configService = context.read<ConfigService>();
    final syncService = context.read<SyncService>();

    if (configService.config != null) {
      final success = await syncService.sync(configService.config!);
      if (success) {
        _refreshController.refreshCompleted();
      } else {
        _refreshController.refreshFailed();
      }
    } else {
      _refreshController.refreshCompleted();
    }
  }

  void _logout() async {
    final configService = context.read<ConfigService>();
    final syncService = context.read<SyncService>();

    await configService.logout();
    syncService.clearSummaries();

    if (mounted) {
      Navigator.of(
        context,
      ).pushReplacement(MaterialPageRoute(builder: (_) => const LoginScreen()));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      body: Consumer2<ConfigService, SyncService>(
        builder: (context, configService, syncService, child) {
          return SmartRefresher(
            controller: _refreshController,
            enablePullDown: true,
            onRefresh: _onRefresh,
            child: CustomScrollView(
              slivers: [
                SliverAppBar(
                  expandedHeight: 180.0,
                  pinned: true,
                  flexibleSpace: FlexibleSpaceBar(
                    title: Text(
                      'Mail Agent',
                      style: GoogleFonts.inter(
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    background: Container(
                      decoration: const BoxDecoration(
                        gradient: LinearGradient(
                          colors: [Color(0xFF2C3E50), Color(0xFF4CA1AF)],
                        ),
                      ),
                    ),
                  ),
                  actions: [
                    IconButton(
                      icon: const Icon(Icons.settings_outlined),
                      onPressed: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (_) => const ConfigScreen(),
                          ),
                        );
                      },
                    ),
                    IconButton(
                      icon: const Icon(Icons.logout),
                      onPressed: _logout,
                    ),
                  ],
                ),

                if (syncService.isSyncing)
                  const SliverToBoxAdapter(child: LinearProgressIndicator()),

                if (syncService.error != null)
                  SliverToBoxAdapter(
                    child: Container(
                      margin: const EdgeInsets.all(16),
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.red.shade50,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: Colors.red.shade200),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(
                                _getErrorIcon(syncService.error!.type),
                                color: Colors.red.shade700,
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Text(
                                  syncService.error!.userMessage,
                                  style: TextStyle(
                                    color: Colors.red.shade700,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ),
                              IconButton(
                                icon: const Icon(Icons.close),
                                color: Colors.red.shade700,
                                onPressed: syncService.clearError,
                              ),
                            ],
                          ),
                          if (syncService.retryCount > 0)
                            Padding(
                              padding: const EdgeInsets.only(top: 8),
                              child: Text(
                                'Retry attempt ${syncService.retryCount}/${SyncService.maxRetries}',
                                style: TextStyle(
                                  color: Colors.red.shade600,
                                  fontSize: 12,
                                ),
                              ),
                            ),
                        ],
                      ),
                    ),
                  ),

                if (syncService.summaries.isEmpty && !syncService.isSyncing)
                  SliverFillRemaining(
                    child: Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            Icons.inbox_outlined,
                            size: 64,
                            color: Colors.grey.shade400,
                          ),
                          const SizedBox(height: 16),
                          Text(
                            'No summaries yet',
                            style: GoogleFonts.inter(
                              fontSize: 18,
                              color: Colors.grey.shade600,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'Pull down to sync',
                            style: GoogleFonts.inter(
                              color: Colors.grey.shade500,
                            ),
                          ),
                        ],
                      ),
                    ),
                  )
                else
                  SliverList(
                    delegate: SliverChildBuilderDelegate((context, index) {
                      final summary = syncService.summaries[index];
                      return _SummaryCard(summary: summary);
                    }, childCount: syncService.summaries.length),
                  ),
              ],
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
          final configService = context.read<ConfigService>();
          final syncService = context.read<SyncService>();
          if (configService.config != null) {
            syncService.sync(configService.config!);
          }
        },
        icon: const Icon(Icons.sync),
        label: const Text('Sync'),
      ),
    );
  }
}

class _SummaryCard extends StatelessWidget {
  final dynamic summary;

  const _SummaryCard({required this.summary});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Text(
                      summary.sender,
                      style: GoogleFonts.inter(
                        fontWeight: FontWeight.bold,
                        color: const Color(0xFF3498DB),
                        fontSize: 13,
                      ),
                    ),
                  ),
                  Text(
                    DateFormat('MMM d, HH:mm').format(summary.receivedAt),
                    style: const TextStyle(color: Colors.grey, fontSize: 11),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                summary.subject,
                style: GoogleFonts.inter(
                  fontWeight: FontWeight.w700,
                  fontSize: 15,
                ),
              ),
              const SizedBox(height: 12),
              Text(
                summary.summaryText,
                style: GoogleFonts.inter(color: Colors.black87, height: 1.5),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
