import java.io.*;
import java.nio.charset.StandardCharsets;
import uk.ac.cam.ch.wwmm.opsin.NameToStructure;
import uk.ac.cam.ch.wwmm.opsin.OpsinResult;

/** One JSON object per input line: the same three facts the web service returns. */
public class OpsinBatch {
    static String esc(String s) {
        if (s == null) return "null";
        StringBuilder b = new StringBuilder("\"");
        for (char c : s.toCharArray()) {
            switch (c) {
                case '"': b.append("\\\""); break;
                case '\\': b.append("\\\\"); break;
                case '\n': b.append("\\n"); break;
                case '\r': b.append("\\r"); break;
                case '\t': b.append("\\t"); break;
                default:
                    if (c < 0x20) b.append(String.format("\\u%04x", (int) c));
                    else b.append(c);
            }
        }
        return b.append('"').toString();
    }
    public static void main(String[] a) throws Exception {
        NameToStructure n2s = NameToStructure.getInstance();
        BufferedReader in = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8));
        PrintStream out = new PrintStream(System.out, true, "UTF-8");
        String line;
        while ((line = in.readLine()) != null) {
            if (line.isEmpty()) continue;
            OpsinResult r = n2s.parseChemicalName(line);
            String smi = r.getStatus() == OpsinResult.OPSIN_RESULT_STATUS.FAILURE ? null : r.getSmiles();
            out.println("{\"query\":" + esc(line) + ",\"status\":\"" + r.getStatus()
                + "\",\"smiles\":" + esc(smi) + ",\"message\":" + esc(r.getMessage()) + "}");
        }
    }
}
