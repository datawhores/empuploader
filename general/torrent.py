from dottorrent import Torrent
from pathlib import Path
import general.arguments as arguments
from base64 import b32encode
from collections import OrderedDict
from datetime import datetime
from hashlib import sha1, md5
import fnmatch
import math
import os
import sys
from urllib.parse import urlparse

from bencoder import bencode

from dottorrent import exceptions
from dottorrent.version import __version__


DEFAULT_CREATOR = "dottorrent/{} (https://github.com/kz26/dottorrent)".format(
    __version__)


MIN_PIECE_SIZE = 2 ** 14
MAX_PIECE_SIZE = 2 ** 26

args=arguments.getargs()
import os


if sys.version_info >= (3, 5) and os.name == 'nt':
    import stat

    def is_hidden_file(path):
        fn = path.split(os.sep)[-1]
        return fn.startswith('.') or \
            bool(os.stat(path).st_file_attributes &
                 stat.FILE_ATTRIBUTE_HIDDEN)
else:
    def is_hidden_file(path):
        fn = path.split(os.sep)[-1]
        return fn.startswith('.')


def print_err(v):
    print(v, file=sys.stderr)

class TorrentOverride(Torrent):
    def __init__(self,inpath,fileSet,trackers=None,private=None)->None:
        super().__init__(inpath,trackers=trackers,private=private)
        self.fileSet=fileSet
    def generate(self, callback=None):
        """
        Computes and stores piece data. Returns ``True`` on success, ``False``
        otherwise.
        :param callback: progress/cancellation callable with method
            signature ``(filename, pieces_completed, pieces_total)``.
            Useful for reporting progress if dottorrent is used in a
            GUI/threaded context, and if torrent generation needs to be cancelled.
            The callable's return value should evaluate to ``True`` to trigger
            cancellation.
        """
        files = []
        single_file = os.path.isfile(self.path)
        if single_file:
            files.append((self.path, os.path.getsize(self.path), {}))
        elif os.path.exists(self.path):
            for x in os.walk(self.path):
                for fn in x[2]:
                    fpath = os.path.normpath(os.path.join(x[0], fn))
                    if fpath not in self.fileSet:
                        continue
                    rel_path = os.path.relpath(fpath, self.path)
                    if any(fnmatch.fnmatch(rel_path, ext) for ext in self.exclude):
                        continue
                    fsize = os.path.getsize(fpath)
                    if fsize and not is_hidden_file(fpath):
                        files.append((fpath, fsize, {}))
        else:
            raise exceptions.InvalidInputException
        total_size = sum([x[1] for x in files])
        if not (len(files) and total_size):
            raise exceptions.EmptyInputException
        # set piece size if not already set
        if self.piece_size is None:
            self.piece_size = self.get_info()[2]
        if files:
            self._pieces = bytearray()
            i = 0
            num_pieces = math.ceil(total_size / self.piece_size)
            pc = 0
            buf = bytearray()
            while i < len(files):
                fe = files[i]
                f = open(fe[0], 'rb')
                if self.include_md5:
                    md5_hasher = md5()
                else:
                    md5_hasher = None
                for chunk in iter(lambda: f.read(self.piece_size), b''):
                    buf += chunk
                    if len(buf) >= self.piece_size \
                            or i == len(files)-1:
                        piece = buf[:self.piece_size]
                        self._pieces += sha1(piece).digest()
                        del buf[:self.piece_size]
                        pc += 1
                        if callback:
                            cancel = callback(fe[0], pc, num_pieces)
                            if cancel:
                                f.close()
                                return False
                    if self.include_md5:
                        md5_hasher.update(chunk)
                if self.include_md5:
                    fe[2]['md5sum'] = md5_hasher.hexdigest()
                f.close()
                i += 1
            # Add pieces from any remaining data
            while len(buf):
                piece = buf[:self.piece_size]
                self._pieces += sha1(piece).digest()
                del buf[:self.piece_size]
                pc += 1
                if callback:
                    cancel = callback(fe[0], pc, num_pieces)
                    if cancel:
                        return False

        # Create the torrent data structure
        data = OrderedDict()
        if len(self.trackers) > 0:
            data['announce'] = self.trackers[0].encode()
            if len(self.trackers) > 1:
                data['announce-list'] = [[x.encode()] for x in self.trackers]
        if self.comment:
            data['comment'] = self.comment.encode()
        if self.created_by:
            data['created by'] = self.created_by.encode()
        else:
            data['created by'] = DEFAULT_CREATOR.encode()
        if self.creation_date:
            data['creation date'] = int(self.creation_date.timestamp())
        if self.web_seeds:
            data['url-list'] = [x.encode() for x in self.web_seeds]
        data['info'] = OrderedDict()
        if single_file:
            data['info']['length'] = files[0][1]
            if self.include_md5:
                data['info']['md5sum'] = files[0][2]['md5sum']
            data['info']['name'] = files[0][0].split(os.sep)[-1].encode()
        else:
            data['info']['files'] = []
            path_sp = self.path.split(os.sep)
            for x in files:
                fx = OrderedDict()
                fx['length'] = x[1]
                if self.include_md5:
                    fx['md5sum'] = x[2]['md5sum']
                fx['path'] = [y.encode()
                              for y in x[0].split(os.sep)[len(path_sp):]]
                data['info']['files'].append(fx)
            data['info']['name'] = path_sp[-1].encode()
        data['info']['pieces'] = bytes(self._pieces)
        data['info']['piece length'] = self.piece_size
        data['info']['private'] = int(self.private)
        if self.source:
            data['info']['source'] = self.source.encode()

        self._data = data
        return True
        

def create_torrent(inputFolder,fileSet,torrentpath):
    Path( os.path.dirname(torrentpath)).mkdir( parents=True, exist_ok=True )
    t=TorrentOverride(inputFolder,fileSet, trackers=[args.prepare.tracker], private=True)
    t.piece_size=min(t.get_info()[2],8388608)
    t.generate()
    with open(torrentpath, 'wb') as f:
        t.save(f)

