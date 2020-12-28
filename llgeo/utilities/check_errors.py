import logging


def log_errs(header, conds, mssgs, terrs):

    logging.basicConfig(level = logging.INFO)
    fatal_flag = False
    logging.info(header)

    for cond, mssg, terr in zip(conds, mssgs, terrs):

        if cond:
                if terr == 'warn':
                    logging.warning(mssg)

                if terr == 'fatal':
                    logging.critical(mssg)
                    fatal_flag = True

    if not fatal_flag:
        logging.info('\n Excecution will continue regardless.')
    else:
        logging.info('\n Excecution cannot continue.')

    return fatal_flag