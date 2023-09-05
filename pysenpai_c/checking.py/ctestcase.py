import os
from pysenpai.checking.testcase import FunctionTestCase
from pysenpai.messages import load_messages, Codes
from pysenpai.output import json_output, output
from pysenpai_c.utils.internal import freopen


class CFunctionTestCase(FunctionTestCase):

    pass



def run_c_cases(category, test_target, st_module, test_cases, lang,
                parent_object=None,
                msg_module="pysenpai",
                custom_msgs={},
                hide_output=True,
                test_recurrence=True,
                validate_exception=False,
                argument_cloner=defaults.default_argument_cloner,
                new_test=defaults.default_new_test,
                grader=defaults.pass_fail_grader):


    fd_o = sys.stdout.fileno()
    fd_i = sys.stdin.fileno()
    orig_stdout = os.fdopen(os.dup(fd_o), "w")
    orig_stdin = os.fdopen(os.dup(fd_i), "r")
    msgs = load_messages(lang, category, module=msg_module)
    msgs.update(custom_msgs)

    prev_res = None
    prev_out = None

    for i, test in enumerate(test_cases):
        json_output.new_run()
        freopen("output", "w", sys.stdout)

        try:
            inps = test.inputs
            fn = input_to_file("\n".join([str(x) for x in inps]))
            freopen(fn, "r", sys.stdin)
        except IndexError:
            inps = []

        if test.args:
            output(
                msgs.get_msg("PrintTestVector", lang), Codes.DEBUG,
                args=test.present_object("arg", test.args),
                call=test.present_call(test_target)
            )
        if test.inputs:
            output(
                msgs.get_msg("PrintInputVector", lang), Codes.DEBUG,
                inputs=test.present_object("input", test.inputs)
            )
        if test.data:
            output(
                msgs.get_msg("PrintTestData", lang), Codes.DEBUG,
                data=test.present_object("data", test.data)
            )

        # Calling the student function
        try:
            res = test.wrap(st_module, test_target)
        except NotCallable as e:
            sys.stdout = save
            output(msgs.get_msg("IsNotFunction", lang), Codes.ERROR, name=e.callable_name)
            return 0
        except BaseException as e:
            if validate_exception:
                res = e
            else:
                os.dup2(orig_stdout.fileno(), sys.stdout.fileno())
                etype, evalue, etrace = sys.exc_info()
                ename = evalue.__class__.__name__
                emsg = str(evalue)
                elineno, eline = get_exception_line(st_module, etrace)
                output(msgs.get_msg(ename, lang, default="GenericErrorMsg"), Codes.ERROR,
                    emsg=emsg,
                    ename=ename
                )
                output(msgs.get_msg("PrintExcLine", lang), Codes.DEBUG,
                    lineno=elineno, line=eline
                )
                test.teardown()
                continue

        # Parsing of output
        os.dup2(orig_stdout.fileno(), sys.stdout.fileno())
        os.dup2(orig_stdin.fileno(), sys.stdin.fileno())
        try:
            with open("output", "r") as f:
                out_content = f.read()
        except UnicodeDecodeError:
            output(msgs.get_msg("OutputEncodingError", lang), ERROR)
            return

        if not hide_output:
            output(msgs.get_msg("PrintStudentOutput", lang), Codes.INFO, output=out_content)

        try:
            st_out = test.parse(out_content)
        except OutputParseError as e:
            output(msgs.get_msg("OutputParseError", lang), Codes.INCORRECT,
                reason=str(e)
            )
            output(msgs.get_msg("OutputPatternInfo", lang), Codes.INFO)
            test.teardown()
            continue

        output(msgs.get_msg("PrintStudentResult", lang), Codes.DEBUG,
            res=test.present_object("res", res),
            parsed=test.present_object("parsed", st_out),
            output=out_content
        )

        # Validate results
        try:
            test.validate_result(res, st_out, out_content)
            output(msgs.get_msg("CorrectResult", lang), Codes.CORRECT)
        except AssertionError as e:
            # Result was incorrect
            output(msgs.get_msg(e, lang, "IncorrectResult"), Codes.INCORRECT)
            output(
                msgs.get_msg("PrintReference", lang),
                Codes.DEBUG,
                ref=test.present_object("ref", test.ref_result)
            )

            output(msgs.get_msg("AdditionalTests", lang), Codes.INFO)

            # Extra feedback
            for msg_key, format_args in test.feedback(res, st_out, out_content):
                output(msgs.get_msg(msg_key, lang), Codes.INFO, **format_args)

        if test.output_validator:
            try:
                test.validate_output(out_content)
                output(msgs.get_msg("CorrectMessage", lang), Codes.CORRECT)
            except AssertionError as e:
                output(msgs.get_msg(e, lang, "IncorrectMessage"), Codes.INCORRECT)
                output(msgs.get_msg("MessageInfo", lang), Codes.INFO)
                output(msgs.get_msg("PrintStudentOutput", lang), Codes.INFO, output=out_content)

        test.teardown()
        prev_res = res
        prev_out = st_out

    return grader(test_cases)








