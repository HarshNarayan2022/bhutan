from transformers import pipeline
from collections import Counter
import json
from pathlib import Path
from datetime import datetime
import numpy as np

class ChatSentimentAnalyzer:
    def __init__(self):
        # Initialize the emotion analysis pipeline with RoBERTa model
        self.analyzer = pipeline("text-classification", 
                               model='bhadresh-savani/roberta-base-emotion', 
                               return_all_scores=True)
        
        # Define emotion categories
        self.emotion_labels = ['anger', 'fear', 'joy', 'love', 'sadness', 'surprise']
        
        # Map emotions to sentiment categories
        self.emotion_to_sentiment = {
            'joy': 'POSITIVE',
            'love': 'POSITIVE',
            'surprise': 'NEUTRAL',
            'anger': 'NEGATIVE',
            'fear': 'NEGATIVE',
            'sadness': 'NEGATIVE'
        }
        
    def analyze_chat_session(self, chat_data):
        """Analyze sentiment for a complete chat session"""
        if isinstance(chat_data, str):
            # If it's a file path, load the data
            with open(chat_data, 'r') as f:
                chat_data = json.load(f)
        
        messages = chat_data.get('messages', [])
        
        # Separate user and assistant messages
        user_messages = []
        assistant_messages = []
        
        for msg in messages:
            if msg['role'] == 'user':
                user_messages.append({
                    'content': msg['content'],
                    'timestamp': msg['timestamp']
                })
            elif msg['role'] == 'assistant':
                assistant_messages.append({
                    'content': msg['content'],
                    'timestamp': msg['timestamp'],
                    'agent': msg.get('agent', 'Unknown')
                })
        
        # Analyze sentiments
        user_sentiments = self._analyze_messages(user_messages, 'user')
        assistant_sentiments = self._analyze_messages(assistant_messages, 'assistant')
        
        # Calculate session metrics
        session_metrics = self._calculate_session_metrics(user_sentiments, assistant_sentiments)
        
        return {
            'user_sentiments': user_sentiments,
            'assistant_sentiments': assistant_sentiments,
            'session_metrics': session_metrics,
            'session_id': chat_data.get('session_id'),
            'user_name': chat_data.get('user_name'),
            'timestamp': datetime.now().isoformat()
        }
    
    def _analyze_messages(self, messages, sender_type):
        """Analyze sentiment for a list of messages"""
        if not messages:
            return []
        
        # Extract just the content for analysis
        contents = [msg['content'] for msg in messages]
        
        results = []
        for msg, content in zip(messages, contents):
            try:
                # Get emotion predictions
                predictions = self.analyzer(content)
                
                # Find the emotion with highest score
                emotion_scores = predictions[0]  # Get first (and only) result
                top_emotion = max(emotion_scores, key=lambda x: x['score'])
                
                # Create emotion distribution
                emotion_dist = {score['label']: round(score['score'], 3) 
                               for score in emotion_scores}
                
                # Map to sentiment
                sentiment = self.emotion_to_sentiment.get(top_emotion['label'], 'NEUTRAL')
                
                results.append({
                    'content': msg['content'],
                    'timestamp': msg.get('timestamp'),
                    'emotion': top_emotion['label'],
                    'emotion_confidence': round(top_emotion['score'], 3),
                    'emotion_distribution': emotion_dist,
                    'sentiment': sentiment,
                    'sender_type': sender_type
                })
            except Exception as e:
                print(f"Error analyzing message: {e}")
                results.append({
                    'content': msg['content'],
                    'timestamp': msg.get('timestamp'),
                    'emotion': 'unknown',
                    'emotion_confidence': 0.0,
                    'emotion_distribution': {},
                    'sentiment': 'NEUTRAL',
                    'sender_type': sender_type
                })
        
        return results
    

    def analyze_limited_data(self, data):
        """Optimized analysis for limited data"""
        try:
            all_messages = []
            session_count = len(data['sessions'])
            
            # Collect all messages
            for session in data['sessions']:
                all_messages.extend(session['messages'])
            
            if not all_messages:
                return {"error": "No messages to analyze"}
            
            # Limit total messages for performance
            all_messages = all_messages[:100]
            
            # Process emotions using the existing analyzer
            emotion_counts = {}
            positive_count = 0
            negative_count = 0
            
            for message in all_messages:
                try:
                    # Get emotion predictions using existing analyzer
                    predictions = self.analyzer(message)
                    emotion_scores = predictions[0]
                    top_emotion = max(emotion_scores, key=lambda x: x['score'])
                    
                    # Count emotions
                    emotion = top_emotion['label']
                    emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                    
                    # Map to sentiment using existing mapping
                    sentiment = self.emotion_to_sentiment.get(emotion, 'NEUTRAL')
                    if sentiment == 'POSITIVE':
                        positive_count += 1
                    elif sentiment == 'NEGATIVE':
                        negative_count += 1
                        
                except Exception as e:
                    print(f"Error processing message: {e}")
                    continue
            
            # Calculate quick metrics
            total_messages = len(all_messages)
            positivity_ratio = positive_count / total_messages if total_messages > 0 else 0
            
            # Determine dominant emotion
            dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0] if emotion_counts else 'unknown'
            
            # Simple trend calculation
            if positive_count > negative_count * 1.5:
                trend = 'IMPROVING'
            elif negative_count > positive_count * 1.5:
                trend = 'DECLINING'
            else:
                trend = 'STABLE'
            
            return {
                'total_sessions': session_count,
                'total_messages_analyzed': total_messages,
                'aggregated_metrics': {
                    'overall_positivity_ratio': positivity_ratio,
                    'dominant_emotion': dominant_emotion,
                    'emotion_distribution': emotion_counts,
                    'total_positive_messages': positive_count,
                    'total_negative_messages': negative_count,
                    'most_common_trend': trend,
                    'trend_distribution': {
                        'IMPROVING': 1 if trend == 'IMPROVING' else 0,
                        'STABLE': 1 if trend == 'STABLE' else 0,
                        'DECLINING': 1 if trend == 'DECLINING' else 0
                    }
                }
            }
            
        except Exception as e:
            print(f"Error in limited analysis: {e}")
            return {"error": str(e)}
    
    def _calculate_session_metrics(self, user_sentiments, assistant_sentiments):
        """Calculate overall session metrics"""
        # Extract emotions and sentiments
        user_emotions = [s['emotion'] for s in user_sentiments if s['emotion'] != 'unknown']
        user_sentiment_labels = [s['sentiment'] for s in user_sentiments]
        
        metrics = {
            'user_emotion_distribution': Counter(user_emotions),
            'user_sentiment_distribution': Counter(user_sentiment_labels),
            'assistant_sentiment_distribution': Counter([s['sentiment'] for s in assistant_sentiments]),
            'user_avg_confidence': np.mean([s['emotion_confidence'] for s in user_sentiments]) if user_sentiments else 0,
            'assistant_avg_confidence': np.mean([s['emotion_confidence'] for s in assistant_sentiments]) if assistant_sentiments else 0,
            'total_messages': len(user_sentiments) + len(assistant_sentiments),
            'sentiment_trend': self._calculate_sentiment_trend(user_sentiments),
            'dominant_emotion': Counter(user_emotions).most_common(1)[0][0] if user_emotions else 'unknown'
        }
        
        # Calculate emotional valence
        if user_emotions:
            positive_emotions = sum(1 for e in user_emotions if e in ['joy', 'love'])
            negative_emotions = sum(1 for e in user_emotions if e in ['anger', 'fear', 'sadness'])
            neutral_emotions = sum(1 for e in user_emotions if e in ['surprise'])
            
            total_emotions = len(user_emotions)
            metrics['emotional_valence'] = {
                'positive': round(positive_emotions / total_emotions, 3),
                'negative': round(negative_emotions / total_emotions, 3),
                'neutral': round(neutral_emotions / total_emotions, 3)
            }
        
        # Calculate overall session sentiment
        if user_sentiment_labels:
            positive_count = user_sentiment_labels.count('POSITIVE')
            negative_count = user_sentiment_labels.count('NEGATIVE')
            metrics['overall_session_sentiment'] = 'POSITIVE' if positive_count > negative_count else 'NEGATIVE'
            metrics['positivity_ratio'] = positive_count / len(user_sentiment_labels) if user_sentiment_labels else 0
        
        return metrics
    
    def _calculate_sentiment_trend(self, sentiments):
        """Calculate how sentiment changes over time"""
        if len(sentiments) < 2:
            return 'stable'
        
        # Convert sentiments to numeric values based on emotional valence
        sentiment_values = []
        for s in sentiments:
            if s['emotion'] in ['joy', 'love']:
                sentiment_values.append(1)
            elif s['emotion'] in ['anger', 'fear', 'sadness']:
                sentiment_values.append(-1)
            else:
                sentiment_values.append(0)
        
        # Calculate trend using simple linear regression
        x = np.arange(len(sentiment_values))
        y = np.array(sentiment_values)
        
        # Calculate slope
        if len(x) > 1:
            slope = np.polyfit(x, y, 1)[0]
            
            if slope > 0.1:
                return 'improving'
            elif slope < -0.1:
                return 'declining'
            else:
                return 'stable'
        
        return 'stable'
    
    def analyze_user_history(self, user_name, sessions_dir='chat_sessions'):
        """Analyze all chat sessions for a specific user"""
        sessions_path = Path(sessions_dir)
        user_files = list(sessions_path.glob(f"chat_{user_name}_*.json"))
        
        all_analyses = []
        for file_path in sorted(user_files):
            try:
                analysis = self.analyze_chat_session(str(file_path))
                all_analyses.append(analysis)
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
        
        # Aggregate metrics across all sessions
        if all_analyses:
            aggregated_metrics = self._aggregate_user_metrics(all_analyses)
            return {
                'user_name': user_name,
                'total_sessions': len(all_analyses),
                'session_analyses': all_analyses,
                'aggregated_metrics': aggregated_metrics
            }
        
        return None
    
    def _aggregate_user_metrics(self, analyses):
        """Aggregate metrics across multiple sessions"""
        total_positive = 0
        total_negative = 0
        total_neutral = 0
        all_trends = []
        all_emotions = []
        
        for analysis in analyses:
            metrics = analysis['session_metrics']
            user_dist = metrics['user_sentiment_distribution']
            emotion_dist = metrics['user_emotion_distribution']
            
            total_positive += user_dist.get('POSITIVE', 0)
            total_negative += user_dist.get('NEGATIVE', 0)
            total_neutral += user_dist.get('NEUTRAL', 0)
            all_trends.append(metrics['sentiment_trend'])
            
            # Collect all emotions
            for emotion, count in emotion_dist.items():
                all_emotions.extend([emotion] * count)
        
        trend_counts = Counter(all_trends)
        emotion_counts = Counter(all_emotions)
        
        return {
            'total_positive_messages': total_positive,
            'total_negative_messages': total_negative,
            'total_neutral_messages': total_neutral,
            'overall_positivity_ratio': total_positive / (total_positive + total_negative + total_neutral) if (total_positive + total_negative + total_neutral) > 0 else 0,
            'trend_distribution': dict(trend_counts),
            'most_common_trend': trend_counts.most_common(1)[0][0] if trend_counts else 'unknown',
            'emotion_distribution': dict(emotion_counts),
            'dominant_emotion': emotion_counts.most_common(1)[0][0] if emotion_counts else 'unknown'
        }

# Backward compatibility wrapper
def analyze_sentiments(messages, label):
    analyzer = ChatSentimentAnalyzer()
    results = []
    
    for msg in messages:
        try:
            predictions = analyzer.analyzer(msg)
            emotion_scores = predictions[0]
            top_emotion = max(emotion_scores, key=lambda x: x['score'])
            
            results.append({
                'label': top_emotion['label'],
                'score': top_emotion['score']
            })
            print(f"Message: {msg}")
            print(f"Emotion: {top_emotion['label']} (Score: {round(top_emotion['score'], 2)})")
            print(f"All emotions: {[(e['label'], round(e['score'], 3)) for e in emotion_scores]}\n")
        except:
            pass
    
    return results

def summarize_sentiments(sentiments, label):
    labels = [r["label"] for r in sentiments]
    summary = Counter(labels)
    print(f"📊 {label} Emotion Summary: {dict(summary)}\n")
    return summary

# Example usage
if __name__ == "__main__":
    analyzer = ChatSentimentAnalyzer()
    
    # Test the emotion classifier
    test_messages = [
        "I love using transformers. The best part is wide range of support and its easy to use",
        "I am feeling very anxious about the upcoming exam",
        "This makes me so angry and frustrated",
        "I'm surprised by how well this works"
    ]
    
    print("Testing emotion analysis:")
    print("-" * 50)
    for msg in test_messages:
        predictions = analyzer.analyzer(msg)
        emotion_scores = predictions[0]
        top_emotion = max(emotion_scores, key=lambda x: x['score'])
        print(f"Message: {msg}")
        print(f"Top emotion: {top_emotion['label']} ({round(top_emotion['score'], 3)})")
        print(f"All emotions: {[(e['label'], round(e['score'], 3)) for e in emotion_scores]}")
        print("-" * 50)