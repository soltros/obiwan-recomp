// Export native script-name registration stubs observed in the Obi-Wan XBE.
// Run with Ghidra's analyzeHeadless -postScript option against default.xbe.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSpace;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.scalar.Scalar;
import java.util.LinkedHashMap;
import java.util.Map;

public class ExportScriptRegistrations extends GhidraScript {
    private static final long[] TABLES = { 0x00422900L, 0x00422B60L };
    private static final long REGISTRATION_HELPER = 0x00159F70L;
    private static final long CODE_MIN = 0x00345000L;
    private static final long CODE_MAX = 0x00350000L;
    private static final long STRING_MIN = 0x003C8000L;
    private static final long STRING_MAX = 0x003D0000L;

    @Override
    public void run() throws Exception {
        AddressSpace space = currentProgram.getAddressFactory().getDefaultAddressSpace();
        Map<String, String> registrations = new LinkedHashMap<>();
        for (long table : TABLES) {
            for (int index = 0; index < 500; index++) {
                int rawTarget = getInt(space.getAddress(table + index * 4L));
                long target = Integer.toUnsignedLong(rawTarget);
                if (target < CODE_MIN || target > CODE_MAX) {
                    break;
                }
                Instruction instruction = currentProgram.getListing()
                        .getInstructionAt(space.getAddress(target));
                boolean callsRegistrar = false;
                String registeredName = "";
                for (int n = 0; instruction != null && n < 40; n++, instruction = instruction.getNext()) {
                    if (instruction.getFlowType().isCall()) {
                        for (Address flow : instruction.getFlows()) {
                            if (flow.equals(space.getAddress(REGISTRATION_HELPER))) {
                                callsRegistrar = true;
                            }
                        }
                    }
                    for (int operand = 0; operand < instruction.getNumOperands(); operand++) {
                        for (Object object : instruction.getOpObjects(operand)) {
                            if (object instanceof Scalar) {
                                long value = ((Scalar) object).getUnsignedValue();
                                if (value >= STRING_MIN && value < STRING_MAX) {
                                    String candidate = readAscii(space, value);
                                    if (!candidate.isEmpty()) {
                                        registeredName = candidate;
                                    }
                                }
                            }
                        }
                    }
                    if (instruction.getMnemonicString().startsWith("RET")) {
                        break;
                    }
                }
                if (callsRegistrar) {
                    String key = String.format("%08X\t%s", target, registeredName);
                    registrations.put(key, key);
                }
            }
        }
        for (String registration : registrations.values()) {
            println("REGISTRATION\t" + registration);
        }
        println("TOTAL\t" + registrations.size());
    }

    private String readAscii(AddressSpace space, long address) throws Exception {
        StringBuilder result = new StringBuilder();
        for (int offset = 0; offset < 64; offset++) {
            int value = getByte(space.getAddress(address + offset)) & 0xff;
            if (value == 0) {
                break;
            }
            if (value < 32 || value > 126) {
                return "";
            }
            result.append((char) value);
        }
        return result.toString();
    }
}
