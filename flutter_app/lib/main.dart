import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

void main() {
  runApp(const MailAgentApp());
}

class MailAgentApp extends StatelessWidget {
  const MailAgentApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Mail Agent',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF2C3E50),
          primary: const Color(0xFF2C3E50),
          secondary: const Color(0xFF3498DB),
        ),
        textTheme: GoogleFonts.interTextTheme(),
      ),
      home: const DashboardScreen(),
    );
  }
}

class Summary {
  final String sender;
  final String subject;
  final String content;
  final String time;

  Summary({
    required this.sender,
    required this.subject,
    required this.content,
    required this.time,
  });

  factory Summary.fromJson(Map<String, dynamic> json) {
    return Summary(
      sender: json['sender'],
      subject: json['subject'],
      content: json['summary_text'],
      time: json['received_at'],
    );
  }
}

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  // CONFIGURATION: Replace with your Ubuntu Server IP
  final String serverIp = "202.137.147.5"; 
  
  List<Summary> _summaries = [];
  bool _isLoading = true;
  String _error = "";

  @override
  void initState() {
    super.initState();
    _fetchSummaries();
  }

  Future<void> _fetchSummaries() async {
    setState(() {
      _isLoading = true;
      _error = "";
    });

    try {
      final response = await http.get(
        Uri.parse('http://$serverIp:8000/summaries'),
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        List jsonResponse = json.decode(response.body);
        setState(() {
          _summaries = jsonResponse.map((s) => Summary.fromJson(s)).toList();
          _isLoading = false;
        });
      } else {
        setState(() {
          _error = "Server Error: ${response.statusCode}";
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = "Connection Failed. Is the Ubuntu API running?";
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      body: RefreshIndicator(
        onRefresh: _fetchSummaries,
        child: CustomScrollView(
          slivers: [
            SliverAppBar(
              expandedHeight: 180.0,
              pinned: true,
              flexibleSpace: FlexibleSpaceBar(
                title: Text(
                  'Mail Agent',
                  style: GoogleFonts.inter(fontWeight: FontWeight.bold, color: Colors.white),
                ),
                background: Container(
                  decoration: const BoxDecoration(
                    gradient: LinearGradient(
                      colors: [Color(0xFF2C3E50), Color(0xFF4CA1AF)],
                    ),
                  ),
                ),
              ),
            ),
            
            if (_isLoading)
              const SliverFillRemaining(
                child: Center(child: CircularProgressIndicator()),
              )
            else if (_error.isNotEmpty)
              SliverFillRemaining(
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error_outline, size: 48, color: Colors.red),
                      const SizedBox(height: 16),
                      Text(_error, textAlign: TextAlign.center),
                      ElevatedButton(onPressed: _fetchSummaries, child: const Text("Retry")),
                    ],
                  ),
                ),
              )
            else if (_summaries.isEmpty)
              const SliverFillRemaining(
                child: Center(child: Text("No summaries found for today.")),
              )
            else
              SliverList(
                delegate: SliverChildBuilderDelegate(
                  (context, index) {
                    final summary = _summaries[index];
                    return Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
                      child: Card(
                        elevation: 0,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16),
                          side: BorderSide(color: Colors.grey.shade200),
                        ),
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
                                  Text(summary.time, style: const TextStyle(color: Colors.grey, fontSize: 10)),
                                ],
                              ),
                              const SizedBox(height: 8),
                              Text(summary.subject, style: GoogleFonts.inter(fontWeight: FontWeight.w700, fontSize: 15)),
                              const SizedBox(height: 12),
                              Text(summary.content, style: GoogleFonts.inter(color: Colors.black87, height: 1.5)),
                            ],
                          ),
                        ),
                      ),
                    );
                  },
                  childCount: _summaries.length,
                ),
              ),
          ],
        ),
      ),
    );
  }
}
