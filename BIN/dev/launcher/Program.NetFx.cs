using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

namespace InyfinnLauncher
{
    internal static class Program
    {
        [STAThread]
        private static int Main(string[] args)
        {
            var root = AppDomain.CurrentDomain.BaseDirectory.TrimEnd(
                Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
            var binDir = Path.Combine(root, "BIN");
            var appExe = Path.Combine(binDir, "InyfinnPhotoResizer.exe");
            var internalDir = Path.Combine(binDir, "_internal");

            if (!File.Exists(appExe) || !Directory.Exists(internalDir))
            {
                MessageBox.Show(
                    "Brak programu:\n" + appExe + "\n\nUruchom BIN\\build.bat aby przebudować.",
                    "Inyfinn Photo Resizer",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error);
                return 1;
            }

            var psi = new ProcessStartInfo
            {
                FileName = appExe,
                WorkingDirectory = binDir,
                UseShellExecute = false,
            };
            if (args != null && args.Length > 0)
            {
                psi.Arguments = string.Join(" ", Array.ConvertAll(args, QuoteArg));
            }

            var proc = Process.Start(psi);
            if (proc == null)
            {
                return 1;
            }
            using (proc)
            {
                proc.WaitForExit();
                return proc.ExitCode;
            }
        }

        private static string QuoteArg(string arg)
        {
            if (string.IsNullOrEmpty(arg))
            {
                return "\"\"";
            }
            if (arg.IndexOfAny(new[] { ' ', '\t', '"' }) < 0)
            {
                return arg;
            }
            return "\"" + arg.Replace("\"", "\\\"") + "\"";
        }
    }
}
