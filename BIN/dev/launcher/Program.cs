using System.Diagnostics;
using System.Windows.Forms;

var root = AppContext.BaseDirectory.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
var binDir = Path.Combine(root, "BIN");
var appExe = Path.Combine(binDir, "InyfinnPhotoResizer.exe");
var internalDir = Path.Combine(binDir, "_internal");

if (!File.Exists(appExe) || !Directory.Exists(internalDir))
{
    MessageBox.Show(
        $"Brak programu:\n{appExe}\n\nUruchom BIN\\build.bat aby przebudować.",
        "Inyfinn Photo Resizer",
        MessageBoxButtons.OK,
        MessageBoxIcon.Error);
    return 1;
}

var psi = new ProcessStartInfo(appExe)
{
    WorkingDirectory = binDir,
    UseShellExecute = false,
};
foreach (var arg in args)
{
    psi.ArgumentList.Add(arg);
}

using var proc = Process.Start(psi);
return proc is null ? 1 : proc.WaitForExit();
