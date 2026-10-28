using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

/// Renders KismetSerializer JSON statements as compact, readable pseudocode lines ("@N text").
static class Pseudo
{
    static readonly HashSet<string> Noise = new() { "Tracepoint", "WireTracepoint", "InstrumentationEvent", "EndOfScript" };

    static readonly Dictionary<string, string> BinaryOps = new()
    {
        ["Add"] = "+", ["Subtract"] = "-", ["Multiply"] = "*", ["Divide"] = "/", ["Percent"] = "%",
        ["Less"] = "<", ["Greater"] = ">", ["LessEqual"] = "<=", ["GreaterEqual"] = ">=",
        ["EqualEqual"] = "==", ["NotEqual"] = "!=",
    };

    static string Short(string? path)
    {
        if (string.IsNullOrEmpty(path)) return "?";
        var tail = path.Contains('/') ? path[(path.LastIndexOf('/') + 1)..] : path;
        return tail.Contains('.') ? tail[(tail.LastIndexOf('.') + 1)..] : tail;
    }

    static string S(JToken? t) => t?.Type == JTokenType.String ? (string)t! : t?.ToString(Formatting.None) ?? "?";

    static string Params(JToken e) =>
        string.Join(", ", (e["Parameters"] as JArray ?? new JArray()).Select(X));

    static string VarName(JToken e) => S(e["Variable Name"] ?? e["Property Name"]);

    public static string X(JToken? t)
    {
        if (t is not JObject e) return t?.ToString(Formatting.None) ?? "?";
        var inst = S(e["Inst"]);
        switch (inst)
        {
            case "LocalVariable": case "InstanceVariable": case "LocalOutVariable":
                return VarName(e);
            case "DefaultVariable":
                return "Default." + VarName(e);
            case "Context": case "Context_FailSilent": case "ClassContext": case "InterfaceContext":
            {
                var ctx = e["Context"];
                var ctxObj = ctx is JObject co && S(co["Inst"]) == "ObjectConst" ? Short(S(co["Object"])) : null;
                if (ctxObj == "Default__KismetArrayLibrary") return ArrayCall(e["Expression"] as JObject);
                if (ctxObj != null && ctxObj.StartsWith("Default__") && e["Expression"] is JObject call
                    && (S(call["Inst"]).EndsWith("Function")))
                {
                    var lib = ctxObj["Default__".Length..];
                    if (lib.EndsWith("_C")) lib = lib[..^2];
                    return MathCall(lib, S(call["Function"] ?? call["FunctionName"]), call);
                }
                var left = X(ctx);
                return left == "null" ? X(e["Expression"]) : $"{left}.{X(e["Expression"])}";
            }
            case "StructMemberContext":
                return $"{X(e["StructExpression"])}.{S(e["Property Name"] ?? e["StructMemberExpression"])}";
            case "Let": case "LetObj": case "LetBool": case "LetWeakObjPtr": case "LetDelegate": case "LetMulticastDelegate":
                return $"{X(e["Variable"])} = {X(e["Expression"])}";
            case "LetValueOnPersistentFrame":
                return $"{S(e["Property Name"])} = {X(e["Expression"])}";
            case "CallMath":
                return MathCall(Short(S(e["ContextClass"])), S(e["Function"]), e);
            case "FinalFunction": case "LocalFinalFunction": case "VirtualFunction": case "LocalVirtualFunction":
                return $"{S(e["Function"] ?? e["FunctionName"])}({Params(e)})";
            case "CallMulticastDelegate":
                return $"{X(e["Delegate"])}.Broadcast({Params(e)})";
            case "AddMulticastDelegate":
                return $"{X(e["Delegate"])} += {X(e["DelegateToAdd"])}";
            case "RemoveMulticastDelegate":
                return $"{X(e["Delegate"])} -= {X(e["DelegateToAdd"])}";
            case "ClearMulticastDelegate":
                return $"{X(e["DelegateToClear"])}.Clear()";
            case "BindDelegate":
                return $"bind({S(e["FunctionName"])})";
            case "InstanceDelegate":
                return $"&{S(e["FunctionName"])}";
            case "JumpIfNot":
                return $"if !({X(e["Condition"])}) goto @{S(e["Offset"])}";
            case "Jump":
                return $"goto @{S(e["Offset"])}";
            case "ComputedJump":
                return $"switch-entry {X(e["OffsetExpression"])}";
            case "PushExecutionFlow":
                return $"push-flow @{S(e["Offset"])}";
            case "PopExecutionFlow":
                return "pop-flow";
            case "PopExecutionFlowIfNot":
                return $"if !({X(e["Condition"])}) pop-flow";
            case "Return":
            {
                var r = X(e["Expression"]);
                return r == "Nothing" ? "return" : $"return {r}";
            }
            case "Nothing": case "NothingInt32":
                return "Nothing";
            case "IntConst": case "FloatConst": case "DoubleConst": case "ByteConst": case "IntConstByte":
            case "Int64Const": case "UInt64Const": case "BitFieldConst":
                return S(e["Value"]);
            case "IntZero": return "0";
            case "IntOne": return "1";
            case "True": return "true";
            case "False": return "false";
            case "NameConst": return $"'{S(e["Value"])}'";
            case "StringConst": case "UnicodeStringConst": return JsonConvert.ToString(S(e["Value"]));
            case "TextConst":
            {
                var v = e["Value"];
                var text = v is JObject vo ? S(vo["SourceString"] ?? vo["LiteralString"] ?? vo["KeyString"]) : S(v);
                return $"TEXT({JsonConvert.ToString(text)})";
            }
            case "ObjectConst": return Short(S(e["Object"]));
            case "SoftObjectConst": return $"soft({X(e["Value"])})";
            case "NoObject": case "NoInterface": return "null";
            case "Self": return "self";
            case "SkipOffsetConst": return $"@{S(e["Value"])}";
            case "StructConst":
            {
                var props = e["Properties"] as JObject;
                var vals = props == null ? "" : string.Join(", ", props.Properties().SelectMany(p =>
                    p.Value is JArray a ? a.Select(X) : new[] { X(p.Value) }));
                return $"{Short(S(e["Struct"]))}{{{vals}}}";
            }
            case "VectorConst": case "Vector3fConst":
                return $"Vec({S(e["X"])}, {S(e["Y"])}, {S(e["Z"])})";
            case "RotationConst":
                return $"Rot(P={S(e["Pitch"])}, Y={S(e["Yaw"])}, R={S(e["Roll"])})";
            case "TransformConst":
            {
                var rest = new JObject(e.Properties().Where(p => p.Name != "Inst"));
                return $"Transform{rest.ToString(Formatting.None)}";
            }
            case "ArrayConst": case "SetConst":
                return "[" + string.Join(", ", (e["Values"] as JArray ?? new JArray()).Select(X)) + "]";
            case "SetArray":
                return $"{X(e["LeftSideExpression"])} = [" + string.Join(", ", (e["Values"] as JArray ?? new JArray()).Select(X)) + "]";
            case "DynamicCast": case "MetaCast": case "ObjToInterfaceCast": case "CrossInterfaceCast": case "InterfaceToObjCast":
                return $"Cast<{Short(S(e["Class"] ?? e["ClassPtr"] ?? e["InterfaceClass"]))}>({X(e["Expression"] ?? e["Target"])})";
            case "PrimitiveCast":
                return X(e["Expression"]);
            case "ArrayGetByRef":
                return $"{X(e["ArrayVariable"])}[{X(e["ArrayIndex"])}]";
            case "SwitchValue":
            {
                var cases = string.Join("; ", (e["Cases"] as JArray ?? new JArray())
                    .Select(c => $"{X(c["CaseIndexValueTerm"])}: {X(c["CaseTerm"])}"));
                return $"switch({X(e["IndexTerm"])}) {{{cases}; default: {X(e["DefaultTerm"])}}}";
            }
        }
        var trimmed = new JObject(e.Properties().Where(p => p.Name != "Variable Outer" && p.Name != "Property Outer"));
        return trimmed.ToString(Formatting.None);
    }

    // Library functions whose result arrives through an out-parameter: (function, index of the out arg).
    static readonly Dictionary<string, int> OutParamCalls = new()
    {
        ["GetAllActorsOfClass"] = 2, ["GetAllActorsWithTag"] = 2, ["GetAllActorsOfClassWithTag"] = 3,
        ["GetAllWidgetsOfClass"] = 1,
    };

    static string MathCall(string cls, string fn, JToken e)
    {
        var args = (e["Parameters"] as JArray ?? new JArray()).Select(X).ToList();
        if (OutParamCalls.TryGetValue(fn, out var outIdx) && outIdx < args.Count)
        {
            var target = args[outIdx];
            var rest = args.Where((_, k) => k != outIdx);
            return $"{target} = {cls}::{fn}({string.Join(", ", rest)})";
        }
        if (cls == "KismetMathLibrary")
        {
            if (fn == "Not_PreBool" && args.Count == 1) return $"!{Wrap(args[0])}";
            if (fn == "BooleanAND" && args.Count == 2) return $"({args[0]} && {args[1]})";
            if (fn == "BooleanOR" && args.Count == 2) return $"({args[0]} || {args[1]})";
            var m = Regex.Match(fn, @"^([A-Za-z]+)_[A-Za-z0-9]+$");
            if (m.Success && args.Count == 2 && BinaryOps.TryGetValue(m.Groups[1].Value, out var op))
                return $"({args[0]} {op} {args[1]})";
            // The Conv_ calls (autocasts such as Conv_VectorToRotator, "Rotation From X Vector") are printed like every other call:
            // they change the value, and a port written from a pseudocode that hid them would not compile or would pick another conversion.
        }
        return $"{cls}::{fn}({string.Join(", ", args)})";
    }

    static string ArrayCall(JObject? call)
    {
        if (call == null) return "?";
        var fn = S(call["Function"] ?? call["FunctionName"]);
        var args = (call["Parameters"] as JArray ?? new JArray()).Select(X).ToList();
        if (fn == "Array_Get" && args.Count == 3) return $"{args[2]} = {args[0]}[{args[1]}]";
        if (fn == "Array_Length" && args.Count == 1) return $"{args[0]}.Num()";
        if (fn.StartsWith("Array_") && args.Count >= 1)
            return $"{args[0]}.{fn["Array_".Length..]}({string.Join(", ", args.Skip(1))})";
        return $"{fn}({string.Join(", ", args)})";
    }

    // Blueprint variable names may contain spaces ("Player Finish Order"), so spaces count as part of a name.
    static bool IsSimple(string s) => Regex.IsMatch(s, @"^[\w.\[\]' ]+(\(\))?$");

    static int MatchingParen(string s, int open)
    {
        int depth = 0;
        for (int k = open; k < s.Length; k++)
        {
            if (s[k] == '(') depth++;
            else if (s[k] == ')' && --depth == 0) return k;
        }
        return -1;
    }

    static bool IsWrapped(string s) => s.Length > 1 && s[0] == '(' && MatchingParen(s, 0) == s.Length - 1;

    static string Wrap(string s) => IsSimple(s) || IsWrapped(s) ? s : $"({s})";

    /// "((a + b))" -> "(a + b)": drop a paren pair whose whole content is itself one paren group.
    static string StripRedundantParens(string s)
    {
        for (int i = 0; i < s.Length; i++)
        {
            if (s[i] != '(' || i + 1 >= s.Length || s[i + 1] != '(') continue;
            int close = MatchingParen(s, i);
            int innerClose = MatchingParen(s, i + 1);
            if (close > 0 && innerClose == close - 1)
            {
                s = s.Remove(close, 1).Remove(i, 1);
                i--;
            }
        }
        return s;
    }

    record Line(int Offset, string Text);

    static readonly Regex FoldableDef = new(@"^(CallFunc_\w+|K2Node_DynamicCast_bSuccess\w*) = (.+)$");
    static readonly Regex TargetRef = new(@"@(\d+)");

    /// Render a function's statements: drop noise, fold single-use temporaries, collapse ForEach macros.
    public static List<string> Render(JArray statements)
    {
        var lines = new List<Line>();
        foreach (var tok in statements)
        {
            if (tok is not JObject stmt || Noise.Contains(S(stmt["Inst"]))) continue;
            lines.Add(new Line(stmt["StatementIndex"]?.Value<int>() ?? -1, X(stmt)));
        }

        var alias = new Dictionary<int, int>();
        void Drop(int i)
        {
            if (i + 1 < lines.Count) alias[lines[i].Offset] = lines[i + 1].Offset;
            lines.RemoveAt(i);
        }

        bool changed = true;
        while (changed)
        {
            changed = false;
            for (int i = 0; i < lines.Count; i++)
            {
                var m = FoldableDef.Match(lines[i].Text);
                if (!m.Success) continue;
                var name = m.Groups[1].Value;
                var expr = m.Groups[2].Value;
                var word = new Regex($@"\b{Regex.Escape(name)}\b");
                if (word.IsMatch(expr)) continue;
                var redefinition = new Regex($@"^{Regex.Escape(name)} = ");

                // The def's live range ends at the next assignment to the same temp.
                int end = lines.Count;
                for (int j = i + 1; j < lines.Count; j++)
                    if (redefinition.IsMatch(lines[j].Text)) { end = j; break; }

                // Dead store: "X = []" immediately overwritten.
                if (end == i + 1 && expr == "[]") { Drop(i); changed = true; break; }

                var uses = Enumerable.Range(i + 1, end - i - 1).Where(j => word.IsMatch(lines[j].Text)).ToList();
                if (uses.Count != 1) continue;
                int u = uses[0];
                if (u - i > 4 || word.Matches(lines[u].Text).Count != 1) continue;

                var replacement = IsSimple(expr) || IsWrapped(expr) ? expr : $"({expr})";
                lines[u] = lines[u] with { Text = word.Replace(lines[u].Text, replacement.Replace("$", "$$"), 1) };
                Drop(i);
                changed = true;
                break;
            }
        }
        // UserDefinedStruct members are stored as "Rank_12_<32 hex>"; keep just "Rank".
        lines = lines.Select(l => l with
        {
            Text = Regex.Replace(StripRedundantParens(l.Text), @"_\d+_[0-9A-F]{32}\b", "")
        }).ToList();

        int Resolve(int off)
        {
            var seen = new HashSet<int>();
            while (alias.TryGetValue(off, out var next) && seen.Add(off)) off = next;
            return off;
        }
        lines = lines.Select(l => l with { Text = TargetRef.Replace(l.Text, mm => "@" + Resolve(int.Parse(mm.Groups[1].Value))) }).ToList();

        lines = CollapseForEach(lines);
        return lines.Select(l => $"  @{l.Offset} {l.Text}").ToList();
    }

    static List<Line> CollapseForEach(List<Line> lines)
    {
        var counter = new Regex(@"^(Temp_int_Loop_Counter_Variable\w*) = 0$");
        var result = new List<Line>(lines);
        for (int i = 0; i + 5 < result.Count; i++)
        {
            var c = counter.Match(result[i].Text);
            if (!c.Success) continue;
            var C = c.Groups[1].Value;
            var idx = Regex.Match(result[i + 1].Text, @"^(Temp_int_Array_Index_Variable\w*) = 0$");
            if (!idx.Success) continue;
            var I = idx.Groups[1].Value;
            var cond = Regex.Match(result[i + 2].Text, $@"^if !\({Regex.Escape(C)} < (.+)\.Num\(\)\) goto @(\d+)$");
            if (!cond.Success) continue;
            if (result[i + 3].Text != $"{I} = {C}") continue;
            var push = Regex.Match(result[i + 4].Text, @"^push-flow @(\d+)$");
            var body = Regex.Match(result[i + 5].Text, @"^goto @(\d+)$");
            if (!push.Success || !body.Success) continue;

            var arr = cond.Groups[1].Value;
            var header = new Line(result[i].Offset,
                $"for ({I} in {arr}) {{ body @{body.Groups[1].Value}; each pass ends in pop-flow }} then @{cond.Groups[2].Value}");
            result.RemoveRange(i, 6);
            result.Insert(i, header);

            int incOffset = int.Parse(push.Groups[1].Value);
            int inc = result.FindIndex(l => l.Offset >= incOffset);
            if (inc >= 0 && inc + 1 < result.Count
                && result[inc].Text == $"{C} = ({C} + 1)"
                && result[inc + 1].Text.StartsWith("goto @"))
            {
                var next = new Line(result[inc].Offset, $"next {I}");
                result.RemoveRange(inc, 2);
                result.Insert(inc, next);
            }
        }
        return result;
    }
}
