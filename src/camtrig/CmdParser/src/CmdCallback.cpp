/* Copyright 2016 Pascal Vizeli <pvizeli@syshack.ch>
 * BSD License
 *
 * https://github.com/pvizeli/CmdParser
 */

#include "CmdCallback.hpp"

void CmdCallbackObject::loopCmdProcessing(CmdParser *      cmdParser,
                                          CmdBufferObject *cmdBuffer,
                                          Stream * serial)
{
    do {
        // read data
        if (cmdBuffer->readFromSerial(serial)) {

            // parse command line
            if (cmdParser->parseCmd(cmdBuffer) != CMDPARSER_ERROR) {
                // search command in store and call function
                if (this->processCmd(cmdParser)) {
                    // FIXME: handling cmd not found
                }
            	cmdBuffer->clear();
            }
        }
    } while (true);
}

bool CmdCallbackObject::processCmd(CmdParser *cmdParser)
{
    char *cmdStr = cmdParser->getCommand();

    // check is commando okay
    if (cmdStr == NULL) {
        return false;
    }

    // search cmd in store
    for (size_t i = 0; this->checkStorePos(i); i++) {

        // compare command with string
        if (this->equalStoreCmd(i, cmdStr)) {
            // call function
            return this->callStoreFunct(i, cmdParser);
        }
    }

    return false;
}
