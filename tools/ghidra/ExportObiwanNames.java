// Export analyzed function entry names from the Obi-Wan XBE project.
// In Ghidra, add this directory to the Script Manager and run the script.
// Headless usage: -postScript ExportObiwanNames.java /path/to/functions.json
// @category ObiWan
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import java.io.PrintWriter;

public class ExportObiwanNames extends GhidraScript {
    private String json(String s) {
        StringBuilder b = new StringBuilder();
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            switch (c) {
                case '"': b.append("\\\""); break;
                case '\\': b.append("\\\\"); break;
                case '\n': b.append("\\n"); break;
                case '\r': b.append("\\r"); break;
                case '\t': b.append("\\t"); break;
                default:
                    if (c < 0x20) b.append(String.format("\\u%04x", (int)c));
                    else b.append(c);
            }
        }
        return b.toString();
    }

    @Override public void run() throws Exception {
        String[] args = getScriptArgs();
        java.io.File output = args.length > 0 ? new java.io.File(args[0])
            : askFile("Save Ghidra function names", "Save");
        try (PrintWriter out = new PrintWriter(output)) {
            out.println("[");
            boolean first = true;
            int count = 0;
            for (Function f : currentProgram.getFunctionManager().getFunctions(true)) {
                if (!first) out.println(",");
                first = false;
                out.print(" {\"address\":\"0x" + f.getEntryPoint().toString().toUpperCase() +
                    "\",\"name\":\"" + json(f.getName()) + "\",\"namespace\":\"\"}");
                count++;
            }
            out.println("\n]");
            println("Exported " + count + " functions to " + output.getAbsolutePath());
        }
    }
}
