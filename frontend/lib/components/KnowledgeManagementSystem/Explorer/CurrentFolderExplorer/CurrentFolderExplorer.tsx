import { useEffect } from "react";

import styles from "./CurrentFolderExplorer.module.scss";
import ProviderCurrentFolder from "./ProviderCurrentFolder/ProviderCurrentFolder";
import QuivrCurrentFolder from "./QuivrCurrentFolder/QuivrCurrentFolder";

import { useKnowledgeContext } from "../../KnowledgeProvider/hooks/useKnowledgeContext";

const CurrentFolderExplorer = (): JSX.Element => {
  const { exploringQuivr, exploredProvider, setExploringQuivr } =
    useKnowledgeContext();

  useEffect(() => {
    setExploringQuivr(true);
  }, []);

  return (
    <div className={styles.current_folder_explorer_container}>
      {exploredProvider || !exploringQuivr ? (
        <ProviderCurrentFolder />
      ) : (
        <QuivrCurrentFolder />
      )}
    </div>
  );
};

export default CurrentFolderExplorer;