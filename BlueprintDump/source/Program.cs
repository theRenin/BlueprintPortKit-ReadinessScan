using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using UAssetAPI;
using UAssetAPI.ExportTypes;
using UAssetAPI.FieldTypes;
using UAssetAPI.Kismet;
using UAssetAPI.PropertyTypes.Objects;
using UAssetAPI.PropertyTypes.Structs;
using UAssetAPI.UnrealTypes;

const string Usage =
    "usage: BlueprintDump [--engine 5.6|5.7|5.8] [--list] [--defaults] [--json|--raw] [--function <Name>]... <path-to-uasset> [more paths...]\n" +
    "  --engine     engine version that saved the assets (default 5.6, or the BLUEPRINTDUMP_ENGINE environment variable)\n" +
    "  (default)    functions as compact pseudocode, one statement per line\n" +
    "  --list       index only: class, parent, interfaces, variables, components, functions with signatures (no bytecode)\n" +
    "  --defaults   also print class-default (CDO) and component-template property values stored in the asset\n" +
    "  --exports    print the stored property values of every object in the package (graph nodes and comments, placed actors, levels)\n" +
    "  --function   only dump the named function(s); repeatable\n" +
    "  --json       compact Kismet JSON, one statement per line (tracepoints removed)\n" +
    "  --raw        full indented Kismet JSON including tracepoints";

var paths = new List<string>();
var functionFilter = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
bool listOnly = false, raw = false, json = false, defaults = false, allExports = false;
// The engine version that saved the assets. 5.6 stays the default so existing callers (bp_snapshot, bp_diff) behave as before.
string engineText = Environment.GetEnvironmentVariable("BLUEPRINTDUMP_ENGINE") ?? "5.6";

for (int i = 0; i < args.Length; i++)
{
    switch (args[i])
    {
        case "--list": listOnly = true; break;
        case "--raw": raw = true; break;
        case "--json": json = true; break;
        case "--defaults": defaults = true; break;
        case "--exports": allExports = true; break;
        case "--engine":
            if (++i >= args.Length) { Console.Error.WriteLine(Usage); return 1; }
            engineText = args[i];
            break;
        case "--function":
            if (++i >= args.Length) { Console.Error.WriteLine(Usage); return 1; }
            functionFilter.Add(args[i]);
            break;
        default: paths.Add(args[i]); break;
    }
}

EngineVersion? engineVersion = engineText switch
{
    "5.6" => EngineVersion.VER_UE5_6,
    "5.7" => EngineVersion.VER_UE5_7,
    "5.8" => EngineVersion.VER_UE5_8,
    _ => null,
};
if (engineVersion == null)
{
    Console.Error.WriteLine($"unknown engine version '{engineText}' (use 5.6, 5.7 or 5.8)");
    return 1;
}
var loadEngineVersion = engineVersion.Value;

if (paths.Count == 0)
{
    Console.Error.WriteLine(Usage);
    return 1;
}

foreach (var path in paths)
{
    if (allExports)
    {
        DumpExports(path, loadEngineVersion);
        continue;
    }
    DumpOne(path, loadEngineVersion, listOnly, raw, json, defaults, functionFilter);
}

return 0;

// UAssetAPI 1.x (the NuGet release) can't read packages saved by UE 5.8 (it runs out of memory in the package metadata block);
// the 2.x build of the pinned master commit can. Say so, so a failure on a 5.8 asset isn't a mystery.
static void PrintLoadFailureHint()
{
    var uassetApiVersion = typeof(UAsset).Assembly.GetName().Version;
    if (uassetApiVersion != null && uassetApiVersion.Major < 2)
    {
        Console.WriteLine("  hint: this build uses UAssetAPI 1.x, which cannot read assets saved by UE 5.8. Use the BlueprintDump build that comes with UAssetAPI 2.x (in this project: python Tools/build_uassetapi.py).");
    }
}

static void DumpExports(string path, EngineVersion loadEngineVersion)
{
    Console.WriteLine($"=== {path} ===");
    UAsset asset;
    try
    {
        asset = LoadAssetAllowingSharedRead(path, loadEngineVersion);
    }
    catch (Exception ex)
    {
        Console.WriteLine($"  failed to load: {ex.GetType().Name}: {ex.Message}");
        PrintLoadFailureHint();
        return;
    }
    foreach (var export in asset.Exports.OfType<NormalExport>())
    {
        Console.WriteLine($"[{export.GetExportClassType()}] {export.ObjectName} (outer: {ResolveName(asset, export.OuterIndex)})");
        foreach (var pd in export.Data ?? new List<PropertyData>())
        {
            Console.WriteLine($"  {CleanName(pd.Name.ToString())} = {FormatValue(asset, pd)}");
        }
    }
    Console.WriteLine();
}

static UAsset LoadAssetAllowingSharedRead(string path, EngineVersion engineVersion)
{
    // The editor keeps its own open handle on these files while the project is
    // loaded, so avoid UAssetAPI's own File.Open (which asks for an exclusive
    // lock) and read the bytes ourselves with FileShare.ReadWrite instead.
    var asset = new UAsset(engineVersion, null, CustomSerializationFlags.None);
    using var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite);
    using var reader = new AssetBinaryReader(stream, asset);
    asset.Read(reader, null, null);
    asset.FilePath = path;
    return asset;
}

static string ResolveName(UAsset asset, FPackageIndex? index)
{
    if (index == null || index.IsNull()) return "(none)";
    return index.IsImport()
        ? index.ToImport(asset).ObjectName.ToString()
        : index.ToExport(asset).ObjectName.ToString();
}

// UserDefinedStruct/Enum member names are mangled as "Name_12_0123456789ABCDEF0123456789ABCDEF".
static string CleanName(string name) => Regex.Replace(name, @"_\d+_[0-9A-F]{32}$", "");

static string DescribeType(UAsset asset, FProperty p) => p switch
{
    FClassProperty c => $"TSubclassOf<{ResolveName(asset, c.MetaClass)}>",
    FSoftClassProperty sc => $"TSoftClassPtr<{ResolveName(asset, sc.MetaClass)}>",
    FSoftObjectProperty so => $"TSoftObjectPtr<{ResolveName(asset, so.PropertyClass)}>",
    FWeakObjectProperty w => $"TWeakObjectPtr<{ResolveName(asset, w.PropertyClass)}>",
    FObjectProperty o => $"{ResolveName(asset, o.PropertyClass)}*",
    FStructProperty s => ResolveName(asset, s.Struct),
    FArrayProperty a => $"TArray<{DescribeType(asset, a.Inner)}>",
    FSetProperty s => $"TSet<{DescribeType(asset, s.ElementProp)}>",
    FMapProperty m => $"TMap<{DescribeType(asset, m.KeyProp)}, {DescribeType(asset, m.ValueProp)}>",
    FEnumProperty e => ResolveName(asset, e.Enum),
    FByteProperty b when b.Enum != null && !b.Enum.IsNull() => ResolveName(asset, b.Enum),
    FInterfaceProperty i => $"TScriptInterface<{ResolveName(asset, i.InterfaceClass)}>",
    FMulticastDelegateProperty md => $"dispatcher({ResolveName(asset, md.SignatureFunction)})",
    FDelegateProperty d => $"delegate({ResolveName(asset, d.SignatureFunction)})",
    _ => p.SerializedType.ToString().Replace("Property", ""),
};

static string VarFlags(FProperty p)
{
    var f = p.PropertyFlags;
    var tags = new List<string>();
    if (f.HasFlag(EPropertyFlags.CPF_Edit) && !f.HasFlag(EPropertyFlags.CPF_DisableEditOnInstance)) tags.Add("instance-editable");
    if (f.HasFlag(EPropertyFlags.CPF_ExposeOnSpawn)) tags.Add("expose-on-spawn");
    if (f.HasFlag(EPropertyFlags.CPF_BlueprintReadOnly)) tags.Add("read-only");
    if (f.HasFlag(EPropertyFlags.CPF_BlueprintAssignable)) tags.Add("assignable");
    if (f.HasFlag(EPropertyFlags.CPF_Net)) tags.Add("replicated");
    if (f.HasFlag(EPropertyFlags.CPF_Transient)) tags.Add("transient");
    return tags.Count > 0 ? $"  [{string.Join(", ", tags)}]" : "";
}

static string FormatValue(UAsset asset, PropertyData pd, int depth = 0)
{
    try
    {
        switch (pd)
        {
            case ObjectPropertyData o:
                return ResolveName(asset, o.Value);
            case StructPropertyData s:
                if (depth > 2 || s.Value == null) return $"{{{s.StructType}}}";
                return "{" + string.Join(", ", s.Value.Select(v => $"{CleanName(v.Name.ToString())}={FormatValue(asset, v, depth + 1)}")) + "}";
            case ArrayPropertyData a:
                if (a.Value == null) return "[]";
                var items = a.Value.Take(8).Select(v => FormatValue(asset, v, depth + 1));
                return "[" + string.Join(", ", items) + (a.Value.Length > 8 ? $", … ({a.Value.Length})" : "") + "]";
            default:
                var raw = pd.RawValue;
                return raw switch
                {
                    null => "null",
                    FPackageIndex idx => ResolveName(asset, idx),
                    _ => raw.ToString() ?? "",
                };
        }
    }
    catch (Exception ex)
    {
        return $"<{ex.GetType().Name}>";
    }
}

static void DumpOne(string path, EngineVersion loadEngineVersion, bool listOnly, bool raw, bool json, bool defaults, HashSet<string> functionFilter)
{
    var noiseInstructions = new HashSet<string> { "Tracepoint", "WireTracepoint", "InstrumentationEvent" };

    Console.WriteLine($"=== {path} ===");

    UAsset asset;
    try
    {
        asset = LoadAssetAllowingSharedRead(path, loadEngineVersion);
    }
    catch (Exception ex)
    {
        Console.WriteLine($"  failed to load: {ex.GetType().Name}: {ex.Message}");
        PrintLoadFailureHint();
        return;
    }

    KismetSerializer.asset = asset;

    foreach (var en in asset.Exports.OfType<EnumExport>())
    {
        Console.WriteLine($"enum {en.ObjectName}:");
        foreach (var entry in en.Enum.Names)
        {
            Console.WriteLine($"  {entry.Item1} = {entry.Item2}");
        }
        var displayNames = en.Data?.FirstOrDefault(d => d.Name.ToString() == "DisplayNameMap");
        if (displayNames != null) Console.WriteLine($"  display names: {FormatValue(asset, displayNames)}");
    }

    foreach (var st in asset.Exports.OfType<UserDefinedStructExport>())
    {
        var fields = st.LoadedProperties ?? Array.Empty<FProperty>();
        Console.WriteLine($"struct {st.ObjectName} ({fields.Length} fields):");
        foreach (var p in fields)
        {
            Console.WriteLine($"  {CleanName(p.Name.ToString())} : {DescribeType(asset, p)}");
        }
    }

    var classExport = asset.Exports.OfType<ClassExport>().FirstOrDefault();
    if (classExport != null)
    {
        Console.WriteLine($"class: {classExport.ObjectName}");
        Console.WriteLine($"parent: {ResolveName(asset, classExport.SuperStruct)}");

        if (classExport.Interfaces is { Length: > 0 })
        {
            Console.WriteLine("implements: " + string.Join(", ",
                classExport.Interfaces.Select(i => ResolveName(asset, new FPackageIndex(i.Class)))));
        }

        var props = classExport.LoadedProperties ?? Array.Empty<FProperty>();
        Console.WriteLine($"variables ({props.Length}):");
        foreach (var p in props)
        {
            Console.WriteLine($"  {p.Name} : {DescribeType(asset, p)}{VarFlags(p)}");
        }
    }

    var components = asset.Exports
        .Where(e => e.ObjectName.ToString().EndsWith("_GEN_VARIABLE"))
        .ToList();
    if (components.Count > 0)
    {
        Console.WriteLine($"components ({components.Count}):");
        foreach (var c in components)
        {
            var name = c.ObjectName.ToString();
            Console.WriteLine($"  {name[..^"_GEN_VARIABLE".Length]} : {c.GetExportClassType()}");
        }
    }

    var functions = asset.Exports.OfType<FunctionExport>().ToList();
    Console.WriteLine($"functions ({functions.Count}):");
    foreach (var fn in functions)
    {
        var fprops = fn.LoadedProperties ?? Array.Empty<FProperty>();
        string Param(FProperty p) => $"{DescribeType(asset, p)} {p.Name}";
        var inputs = fprops.Where(p => p.PropertyFlags.HasFlag(EPropertyFlags.CPF_Parm)
                                    && !p.PropertyFlags.HasFlag(EPropertyFlags.CPF_ReturnParm)
                                    && (!p.PropertyFlags.HasFlag(EPropertyFlags.CPF_OutParm) || p.PropertyFlags.HasFlag(EPropertyFlags.CPF_ReferenceParm)))
                           .Select(Param);
        var outputs = fprops.Where(p => p.PropertyFlags.HasFlag(EPropertyFlags.CPF_ReturnParm)
                                     || (p.PropertyFlags.HasFlag(EPropertyFlags.CPF_OutParm) && !p.PropertyFlags.HasFlag(EPropertyFlags.CPF_ReferenceParm)))
                            .Select(Param).ToList();
        var locals = fprops.Where(p => !p.PropertyFlags.HasFlag(EPropertyFlags.CPF_Parm)).Select(p => p.Name.ToString()).ToList();

        int statements = fn.ScriptBytecode?.Length ?? 0;
        Console.WriteLine($"  {fn.ObjectName}({string.Join(", ", inputs)})" +
                          (outputs.Count > 0 ? $" -> ({string.Join(", ", outputs)})" : "") +
                          $"  [{statements} stmts; {fn.FunctionFlags}]");
        if (locals.Count > 0 && !fn.ObjectName.ToString().StartsWith("ExecuteUbergraph"))
        {
            Console.WriteLine($"      locals: {string.Join(", ", locals)}");
        }
    }

    if (defaults)
    {
        var cdo = asset.Exports.OfType<NormalExport>()
            .FirstOrDefault(e => e.ObjectName.ToString().StartsWith("Default__"));
        foreach (var export in new[] { cdo }.Concat(components.OfType<NormalExport>()).Where(e => e != null))
        {
            Console.WriteLine($"defaults of {export!.ObjectName}:");
            foreach (var pd in export.Data ?? new List<PropertyData>())
            {
                Console.WriteLine($"  {CleanName(pd.Name.ToString())} = {FormatValue(asset, pd)}");
            }
        }
    }

    if (listOnly) { Console.WriteLine(); return; }

    foreach (var fn in functions)
    {
        if (functionFilter.Count > 0 && !functionFilter.Contains(fn.ObjectName.ToString())) continue;

        Console.WriteLine();
        Console.WriteLine($"--- function {fn.ObjectName} ---");
        if (fn.ScriptBytecode == null || fn.ScriptBytecode.Length == 0)
        {
            Console.WriteLine("  (no bytecode)");
            continue;
        }

        JArray statements;
        try
        {
            statements = KismetSerializer.SerializeScript(fn.ScriptBytecode);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"  (failed to serialize bytecode: {ex.Message})");
            continue;
        }

        if (raw)
        {
            Console.WriteLine(statements.ToString(Formatting.Indented));
            continue;
        }

        if (!json)
        {
            foreach (var line in Pseudo.Render(statements)) Console.WriteLine(line);
            continue;
        }

        foreach (var token in statements)
        {
            if (token is not JObject stmt) continue;
            if (noiseInstructions.Contains((string?)stmt["Inst"] ?? "")) continue;

            var index = stmt["StatementIndex"]?.ToString() ?? "?";
            stmt.Remove("StatementIndex");
            Console.WriteLine($"  @{index} {stmt.ToString(Formatting.None)}");
        }
    }

    Console.WriteLine();
}
