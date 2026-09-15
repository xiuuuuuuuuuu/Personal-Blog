using System;
using System.Collections.Generic;
using TMPro;
using UnityEditor;
using UnityEngine;
using UnityEngine.UI;

namespace ProjectTools.Editor
{
    [Serializable]
    internal sealed class TMPToTextFontMapping
    {
        public TMP_FontAsset tmpFont;
        public Font textFont;
    }

    internal sealed class TMPToTextMigrationSettings : ScriptableObject
    {
        private const string AssetPath = "Assets/Editor/TMPToTextMigrationSettings.asset";

        public Font defaultFont;
        public bool useTMPSourceFontAsFallback = true;
        public bool disableRaycastTarget = true;
        public bool enableMaskable = true;
        public bool preserveAutoSize = true;
        public bool supportRichText = true;
        public HorizontalWrapMode horizontalOverflow = HorizontalWrapMode.Overflow;
        public VerticalWrapMode verticalOverflow = VerticalWrapMode.Overflow;
        public List<TMPToTextFontMapping> fontMappings = new List<TMPToTextFontMapping>();

        public static TMPToTextMigrationSettings GetOrCreate()
        {
            var settings = AssetDatabase.LoadAssetAtPath<TMPToTextMigrationSettings>(AssetPath);
            if (settings != null)
                return settings;

            settings = CreateInstance<TMPToTextMigrationSettings>();
            AssetDatabase.CreateAsset(settings, AssetPath);
            AssetDatabase.SaveAssets();
            return settings;
        }

        public Font ResolveFont(TMP_FontAsset tmpFont)
        {
            foreach (TMPToTextFontMapping mapping in fontMappings)
            {
                if (mapping != null && mapping.tmpFont == tmpFont && mapping.textFont != null)
                    return mapping.textFont;
            }

            if (useTMPSourceFontAsFallback && tmpFont != null && tmpFont.sourceFontFile != null)
                return tmpFont.sourceFontFile;

            if (defaultFont != null)
                return defaultFont;

            return GetBuiltinFallbackFont();
        }

        private static Font GetBuiltinFallbackFont()
        {
            Font font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            if (font != null)
                return font;

            return Font.CreateDynamicFontFromOSFont("Arial", 14);
        }
    }

    internal sealed class TMPToTextMigrationSettingsWindow : EditorWindow
    {
        private SerializedObject serializedSettings;
        private Vector2 scrollPosition;

        [MenuItem("Tools/UI/TMP 转 Text 迁移设置")]
        public static void Open()
        {
            GetWindow<TMPToTextMigrationSettingsWindow>("TMP 转 Text");
        }

        private void OnEnable()
        {
            serializedSettings = new SerializedObject(TMPToTextMigrationSettings.GetOrCreate());
        }

        private void OnGUI()
        {
            if (serializedSettings == null)
                serializedSettings = new SerializedObject(TMPToTextMigrationSettings.GetOrCreate());

            serializedSettings.Update();

            scrollPosition = EditorGUILayout.BeginScrollView(scrollPosition);

            EditorGUILayout.LabelField("字体设置", EditorStyles.boldLabel);
            EditorGUILayout.PropertyField(serializedSettings.FindProperty("defaultFont"), new GUIContent("默认 Text 字体"));
            EditorGUILayout.PropertyField(
                serializedSettings.FindProperty("useTMPSourceFontAsFallback"),
                new GUIContent("使用 TMP 源字体兜底", "当 TMP_FontAsset 还保留 sourceFontFile 时，映射缺失会尝试使用它。"));

            EditorGUILayout.Space(8f);
            EditorGUILayout.LabelField("转换设置", EditorStyles.boldLabel);
            EditorGUILayout.PropertyField(serializedSettings.FindProperty("disableRaycastTarget"), new GUIContent("关闭射线检测"));
            EditorGUILayout.PropertyField(serializedSettings.FindProperty("enableMaskable"), new GUIContent("启用 Maskable"));
            EditorGUILayout.PropertyField(serializedSettings.FindProperty("preserveAutoSize"), new GUIContent("迁移 TMP Auto Size"));
            EditorGUILayout.PropertyField(serializedSettings.FindProperty("supportRichText"), new GUIContent("启用 Rich Text"));
            EditorGUILayout.PropertyField(serializedSettings.FindProperty("horizontalOverflow"), new GUIContent("水平 Overflow"));
            EditorGUILayout.PropertyField(serializedSettings.FindProperty("verticalOverflow"), new GUIContent("垂直 Overflow"));

            EditorGUILayout.Space(8f);
            EditorGUILayout.PropertyField(serializedSettings.FindProperty("fontMappings"), new GUIContent("字体映射"), true);

            EditorGUILayout.Space(8f);
            using (new EditorGUILayout.HorizontalScope())
            {
                if (GUILayout.Button("添加选中 TMP 字体"))
                    AddSelectedTMPFontMapping();

                if (GUILayout.Button("保存设置"))
                    AssetDatabase.SaveAssets();
            }

            EditorGUILayout.HelpBox(
                "转换优先级：字体映射 > TMP_FontAsset.sourceFontFile > 默认 Text 字体 > Unity 内置 Arial。旧 Text 不支持 TMP 材质、描边、fallback、sprite 标签和部分 TMP 富文本效果。",
                MessageType.Info);

            EditorGUILayout.EndScrollView();

            if (serializedSettings.ApplyModifiedProperties())
                EditorUtility.SetDirty(serializedSettings.targetObject);
        }

        private void AddSelectedTMPFontMapping()
        {
            var tmp = Selection.activeGameObject != null
                ? Selection.activeGameObject.GetComponent<TextMeshProUGUI>()
                : null;

            if (tmp == null || tmp.font == null)
            {
                EditorUtility.DisplayDialog("没有找到 TMP 字体", "请选择一个带 TextMeshProUGUI 的对象。", "确定");
                return;
            }

            SerializedProperty mappings = serializedSettings.FindProperty("fontMappings");
            int index = mappings.arraySize;
            mappings.InsertArrayElementAtIndex(index);
            SerializedProperty element = mappings.GetArrayElementAtIndex(index);
            element.FindPropertyRelative("tmpFont").objectReferenceValue = tmp.font;
            element.FindPropertyRelative("textFont").objectReferenceValue = tmp.font.sourceFontFile;
            serializedSettings.ApplyModifiedProperties();
        }
    }

    internal static class TMPToTextMigrationTool
    {
        [MenuItem("CONTEXT/TextMeshProUGUI/转换为旧版 Text")]
        private static void ConvertContext(MenuCommand command)
        {
            ConvertOne(command.context as TextMeshProUGUI);
        }

        [MenuItem("GameObject/UI/将 TMP 转换为 Text", false, 49)]
        [MenuItem("GameObject/将 TMP 转换为 Text", false, 49)]
        [MenuItem("Tools/UI/将选中 TMP 转换为 Text")]
        private static void ConvertSelection()
        {
            var tmps = new List<TextMeshProUGUI>();
            var seen = new HashSet<int>();
            foreach (GameObject selected in Selection.gameObjects)
            {
                if (selected == null)
                    continue;

                var selectedTmps = selected.GetComponentsInChildren<TextMeshProUGUI>(true);
                foreach (TextMeshProUGUI tmp in selectedTmps)
                {
                    if (tmp != null && seen.Add(tmp.GetInstanceID()))
                        tmps.Add(tmp);
                }
            }

            if (tmps.Count == 0)
            {
                EditorUtility.DisplayDialog("没有找到 TMP", "当前选择中没有 TextMeshProUGUI 组件。", "确定");
                return;
            }

            int undoGroup = Undo.GetCurrentGroup();
            Undo.SetCurrentGroupName("Convert TMP To Legacy Text");

            foreach (TextMeshProUGUI tmp in tmps)
                ConvertOne(tmp, false);

            Undo.CollapseUndoOperations(undoGroup);
        }

        [MenuItem("GameObject/UI/将 TMP 转换为 Text", true)]
        [MenuItem("GameObject/将 TMP 转换为 Text", true)]
        private static bool CanConvertSelection()
        {
            foreach (GameObject selected in Selection.gameObjects)
            {
                if (selected != null && selected.GetComponentInChildren<TextMeshProUGUI>(true) != null)
                    return true;
            }

            return false;
        }

        private static void ConvertOne(TextMeshProUGUI tmp, bool createUndoGroup = true)
        {
            if (tmp == null)
                return;

            TMPToTextMigrationSettings settings = TMPToTextMigrationSettings.GetOrCreate();
            TMPTextSnapshot snapshot = TMPTextSnapshot.Capture(tmp, settings);
            GameObject gameObject = tmp.gameObject;

            int undoGroup = Undo.GetCurrentGroup();
            if (createUndoGroup)
                Undo.SetCurrentGroupName("Convert TMP To Legacy Text");

            Undo.DestroyObjectImmediate(tmp);
            Text text = Undo.AddComponent<Text>(gameObject);
            snapshot.ApplyTo(text, settings);

            EditorUtility.SetDirty(gameObject);
            if (createUndoGroup)
                Undo.CollapseUndoOperations(undoGroup);
        }

        private struct TMPTextSnapshot
        {
            private string text;
            private Color color;
            private Font font;
            private int fontSize;
            private int minFontSize;
            private int maxFontSize;
            private FontStyle fontStyle;
            private TextAnchor alignment;
            private bool alignByGeometry;
            private bool enableAutoSize;
            private bool supportRichText;
            private float lineSpacing;

            public static TMPTextSnapshot Capture(TextMeshProUGUI tmp, TMPToTextMigrationSettings settings)
            {
                return new TMPTextSnapshot
                {
                    text = tmp.text,
                    color = tmp.color,
                    font = settings.ResolveFont(tmp.font),
                    fontSize = Mathf.Max(1, Mathf.RoundToInt(tmp.fontSize)),
                    minFontSize = Mathf.Max(1, Mathf.RoundToInt(tmp.fontSizeMin)),
                    maxFontSize = Mathf.Max(1, Mathf.RoundToInt(tmp.fontSizeMax)),
                    fontStyle = ConvertFontStyle(tmp.fontStyle),
                    alignment = ConvertAlignment(tmp.horizontalAlignment, tmp.verticalAlignment),
                    alignByGeometry = IsGeometryAligned(tmp.alignment),
                    enableAutoSize = settings.preserveAutoSize && tmp.enableAutoSizing,
                    supportRichText = settings.supportRichText && tmp.richText,
                    lineSpacing = Mathf.Max(0.1f, 1f + tmp.lineSpacing / 100f)
                };
            }

            public void ApplyTo(Text target, TMPToTextMigrationSettings settings)
            {
                target.text = text;
                target.color = color;
                target.font = font;
                target.fontSize = fontSize;
                target.fontStyle = fontStyle;
                target.alignment = alignment;
                target.alignByGeometry = alignByGeometry;
                target.supportRichText = supportRichText;
                target.resizeTextForBestFit = enableAutoSize;
                target.resizeTextMinSize = minFontSize;
                target.resizeTextMaxSize = Mathf.Max(minFontSize, maxFontSize);
                target.horizontalOverflow = settings.horizontalOverflow;
                target.verticalOverflow = settings.verticalOverflow;
                target.lineSpacing = lineSpacing;
                target.maskable = settings.enableMaskable;
                target.raycastTarget = !settings.disableRaycastTarget;
                target.SetAllDirty();
            }
        }

        private static FontStyle ConvertFontStyle(FontStyles style)
        {
            bool bold = (style & FontStyles.Bold) != 0;
            bool italic = (style & FontStyles.Italic) != 0;

            if (bold && italic)
                return FontStyle.BoldAndItalic;

            if (bold)
                return FontStyle.Bold;

            return italic ? FontStyle.Italic : FontStyle.Normal;
        }

        private static TextAnchor ConvertAlignment(
            HorizontalAlignmentOptions horizontal,
            VerticalAlignmentOptions vertical)
        {
            bool left = horizontal == HorizontalAlignmentOptions.Left;
            bool right = horizontal == HorizontalAlignmentOptions.Right;
            bool top = vertical == VerticalAlignmentOptions.Top;
            bool bottom = vertical == VerticalAlignmentOptions.Bottom;

            if (top && left)
                return TextAnchor.UpperLeft;

            if (top && right)
                return TextAnchor.UpperRight;

            if (top)
                return TextAnchor.UpperCenter;

            if (bottom && left)
                return TextAnchor.LowerLeft;

            if (bottom && right)
                return TextAnchor.LowerRight;

            if (bottom)
                return TextAnchor.LowerCenter;

            if (left)
                return TextAnchor.MiddleLeft;

            if (right)
                return TextAnchor.MiddleRight;

            return TextAnchor.MiddleCenter;
        }

        private static bool IsGeometryAligned(TextAlignmentOptions alignment)
        {
            return alignment == TextAlignmentOptions.TopGeoAligned
                || alignment == TextAlignmentOptions.MidlineGeoAligned
                || alignment == TextAlignmentOptions.CaplineGeoAligned
                || alignment == TextAlignmentOptions.BaselineGeoAligned
                || alignment == TextAlignmentOptions.BottomGeoAligned
                || alignment == TextAlignmentOptions.CenterGeoAligned;
        }
    }
}
