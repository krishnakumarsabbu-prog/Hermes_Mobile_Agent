import React from 'react';
import { View, Text, StyleSheet, Platform } from 'react-native';

interface ChatMarkdownProps {
  content: string;
  isUser?: boolean;
}

function renderInline(raw: string, baseStyle: any, isUser: boolean) {
  // Matches ***bold-italic***, **bold**, __bold__, `code`, *italic*, _italic_
  const regex = /(\*\*\*[\s\S]+?\*\*\*|\*\*[\s\S]+?\*\*|__[\s\S]+?__|`[^`]+`|\*[^\s*][^*]*?\*)/g;
  const parts = raw.split(regex);

  return parts.map((part, index) => {
    if (!part) return null;

    if (part.startsWith('***') && part.endsWith('***') && part.length >= 6) {
      return (
        <Text key={index} style={[baseStyle, { fontWeight: '700', fontStyle: 'italic' }]}>
          {part.slice(3, -3)}
        </Text>
      );
    }
    if (
      (part.startsWith('**') && part.endsWith('**') && part.length >= 4) ||
      (part.startsWith('__') && part.endsWith('__') && part.length >= 4)
    ) {
      return (
        <Text
          key={index}
          style={[
            baseStyle,
            {
              fontWeight: '700',
              color: isUser ? '#FFFFFF' : '#111827',
            },
          ]}
        >
          {part.slice(2, -2)}
        </Text>
      );
    }
    if (part.startsWith('`') && part.endsWith('`') && part.length >= 2) {
      return (
        <Text
          key={index}
          style={[
            baseStyle,
            {
              fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
              backgroundColor: isUser ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.06)',
              borderRadius: 4,
              fontSize: 13,
            },
          ]}
        >
          {part.slice(1, -1)}
        </Text>
      );
    }
    if (part.startsWith('*') && part.endsWith('*') && part.length >= 2) {
      return (
        <Text key={index} style={[baseStyle, { fontStyle: 'italic' }]}>
          {part.slice(1, -1)}
        </Text>
      );
    }

    return (
      <Text key={index} style={baseStyle}>
        {part}
      </Text>
    );
  });
}

export function ChatMarkdown({ content, isUser = false }: ChatMarkdownProps) {
  const baseColor = isUser ? '#FFFFFF' : '#1F2937';
  const baseStyle = {
    color: baseColor,
    fontSize: 15,
    lineHeight: 22,
  };

  const lines = content.split('\n');

  return (
    <View style={styles.container}>
      {lines.map((line, idx) => {
        const trimmed = line.trim();

        // Empty line -> spacing between paragraphs
        if (!trimmed) {
          return <View key={idx} style={{ height: 6 }} />;
        }

        // Header 1
        if (line.startsWith('# ')) {
          return (
            <Text
              key={idx}
              style={[
                baseStyle,
                { fontSize: 18, fontWeight: '800', marginTop: 8, marginBottom: 4, color: isUser ? '#FFFFFF' : '#111827' },
              ]}
            >
              {renderInline(line.slice(2), baseStyle, isUser)}
            </Text>
          );
        }

        // Header 2
        if (line.startsWith('## ')) {
          return (
            <Text
              key={idx}
              style={[
                baseStyle,
                { fontSize: 17, fontWeight: '700', marginTop: 6, marginBottom: 4, color: isUser ? '#FFFFFF' : '#111827' },
              ]}
            >
              {renderInline(line.slice(3), baseStyle, isUser)}
            </Text>
          );
        }

        // Header 3
        if (line.startsWith('### ')) {
          return (
            <Text
              key={idx}
              style={[
                baseStyle,
                { fontSize: 16, fontWeight: '700', marginTop: 4, marginBottom: 2, color: isUser ? '#FFFFFF' : '#111827' },
              ]}
            >
              {renderInline(line.slice(4), baseStyle, isUser)}
            </Text>
          );
        }

        // Numbered list: 1. Item
        const numberedMatch = line.match(/^\s*([0-9]+)\.\s+(.*)$/);
        if (numberedMatch) {
          const num = numberedMatch[1];
          const text = numberedMatch[2];
          return (
            <View key={idx} style={styles.listRow}>
              <Text
                style={[
                  baseStyle,
                  {
                    fontWeight: '700',
                    width: 22,
                    color: isUser ? '#FFFFFF' : '#582C83',
                  },
                ]}
              >
                {num}.
              </Text>
              <Text style={[baseStyle, { flex: 1 }]}>
                {renderInline(text, baseStyle, isUser)}
              </Text>
            </View>
          );
        }

        // Bullet list: - Item or * Item or • Item
        const bulletMatch = line.match(/^\s*[-*•]\s+(.*)$/);
        if (bulletMatch) {
          const text = bulletMatch[1];
          return (
            <View key={idx} style={styles.listRow}>
              <Text
                style={[
                  baseStyle,
                  {
                    fontWeight: '700',
                    width: 14,
                    color: isUser ? '#FFFFFF' : '#582C83',
                  },
                ]}
              >
                •
              </Text>
              <Text style={[baseStyle, { flex: 1 }]}>
                {renderInline(text, baseStyle, isUser)}
              </Text>
            </View>
          );
        }

        // Standard text line
        return (
          <Text key={idx} style={baseStyle}>
            {renderInline(line, baseStyle, isUser)}
          </Text>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
  },
  listRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginVertical: 2,
  },
});
