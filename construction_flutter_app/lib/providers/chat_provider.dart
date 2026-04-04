import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/chat_message.dart';
import '../services/ai_service.dart';

final aiServiceProvider = Provider<AiService>((ref) => AiService());

class ChatNotifier extends StateNotifier<List<ChatMessage>> {
  final AiService _aiService;
  ChatNotifier(this._aiService) : super([]);

  Future<void> sendMessage(String text) async {
    final userMsg = ChatMessage(text: text, role: MessageRole.user, timestamp: DateTime.now());
    state = [...state, userMsg];

    try {
      final response = await _aiService.getChatResponse(text);
      final aiMsg = ChatMessage(text: response, role: MessageRole.assistant, timestamp: DateTime.now());
      state = [...state, aiMsg];
    } catch (e) {
      state = [...state, ChatMessage(text: "Error: $e", role: MessageRole.assistant, timestamp: DateTime.now())];
    }
  }
}

final chatProvider = StateNotifierProvider<ChatNotifier, List<ChatMessage>>((ref) {
  return ChatNotifier(ref.watch(aiServiceProvider));
});
